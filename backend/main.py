from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from web3 import Web3
from eth_account import Account
import secrets
import json
import threading
import time

app = FastAPI()

# ---------------------------------------------
# CẤU HÌNH CORS (BẢN CHUẨN ĐỂ FIX LỖI 405)
# ---------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---------------------------------------------

from dotenv import load_dotenv
import os

# Load .env file từ thư mục gốc
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Cấu Hình Blockchain (Mạng Sepolia Testnet)
RPC_URL = os.getenv("SEPOLIA_RPC_URL", "https://eth-sepolia.g.alchemy.com/v2/PsyhKFtlqVE3ENQAZr2Py")
web3 = Web3(Web3.HTTPProvider(RPC_URL))

# Ví Tổng (Master Wallet) - trả tiền Gas và nắm giữ JPYC
MASTER_PK = os.getenv("SEPOLIA_PRIVATE_KEY", "")
if not MASTER_PK:
    raise ValueError("Thiếu SEPOLIA_PRIVATE_KEY trong file .env!")
    
MASTER_ADDRESS = web3.eth.account.from_key(MASTER_PK).address

# Smart Contracts mới deploy trên Sepolia
TOKEN_ADDRESS = web3.to_checksum_address("0x782f6323c6d40a4b6f34adbaf27cfba441ec072e")
CONTRACT_ADDRESS = web3.to_checksum_address("0xf2c183f79f89845c57ae5ab84466c783dc2dc35e")
CHAIN_ID = 11155111

# ── ABIs ──────────────────────────────────────────────────────
ERC20_ABI = [
    {
        "inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}],
        "name": "transfer", "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable", "type": "function"
    },
    {
        "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
        "name": "approve", "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable", "type": "function"
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view", "type": "function"
    },
    {
        "inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}],
        "name": "mint", "outputs": [],
        "stateMutability": "nonpayable", "type": "function"
    }
]

ALOO_ABI = [
    {
        "inputs": [
            {"internalType": "string",  "name": "_orderId", "type": "string"},
            {"internalType": "uint256", "name": "_amount",  "type": "uint256"}
        ],
        "name": "payForSim", "outputs": [],
        "stateMutability": "nonpayable", "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_amount", "type": "uint256"}
        ],
        "name": "withdraw", "outputs": [],
        "stateMutability": "nonpayable", "type": "function"
    }
]

jpyc_contract = web3.eth.contract(
    address=Web3.to_checksum_address(TOKEN_ADDRESS), abi=ERC20_ABI)
aloo_contract = web3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ALOO_ABI)

# ── "Database" in-memory (thực tế dùng PostgreSQL/MySQL) ─────
# { email: {address, pk, balance_jpyc} }
user_db: dict = {}

# ── Nonce Manager (tránh xung đột khi gửi nhiều TX liên tiếp) ─
nonce_lock = threading.Lock()
nonce_cache: dict[str, int] = {}  # {address: last_used_nonce}

def get_next_nonce(address: str) -> int:
    """Lấy nonce an toàn, tránh conflict khi gửi nhiều TX liên tục"""
    with nonce_lock:
        chain_nonce = web3.eth.get_transaction_count(address, "pending")
        cached = nonce_cache.get(address, -1)
        # Lấy max giữa chain và cache+1 để tránh reuse nonce
        nonce = max(chain_nonce, cached + 1)
        nonce_cache[address] = nonce
        return nonce

def get_eip1559_fees() -> dict:
    """Tính gas fee theo chuẩn EIP-1559 cho Sepolia, đẩy cao hơn để đảm bảo confirm nhanh"""
    try:
        latest = web3.eth.get_block("latest")
        base_fee = latest.get("baseFeePerGas", web3.to_wei(1, "gwei"))
        # Priority fee cao hơn bình thường để ưu tiên
        priority_fee = web3.to_wei(3, "gwei")
        # Max fee = 2x base_fee + priority — đủ dư cho 2-3 block tiếp theo
        max_fee = base_fee * 2 + priority_fee
        return {
            "maxFeePerGas": max_fee,
            "maxPriorityFeePerGas": priority_fee,
        }
    except Exception:
        # Fallback nếu node không hỗ trợ EIP-1559
        return {"gasPrice": web3.eth.gas_price * 2}

def wait_with_retry(tx_hash, timeout: int = 180, poll: float = 3.0):
    """Đợi receipt với timeout dài hơn và log tiến trình"""
    hex_h = web3.to_hex(tx_hash)
    start = time.time()
    while True:
        try:
            receipt = web3.eth.get_transaction_receipt(tx_hash)
            if receipt is not None:
                return receipt
        except Exception:
            pass  # Transaction chưa được index
        
        elapsed = time.time() - start
        if elapsed > timeout:
            raise Exception(
                f"Transaction {hex_h} chưa confirm sau {timeout}s. "
                f"TX có thể vẫn đang pending trên mạng — kiểm tra trên Etherscan Sepolia."
            )
        
        # Log mỗi 30 giây
        if int(elapsed) % 30 == 0 and int(elapsed) > 0:
            print(f"  ⏳ Đang đợi confirm... ({int(elapsed)}s / {timeout}s)")
        
        time.sleep(poll)

# ── Helpers ───────────────────────────────────────────────────
def send_tx(fn_call, sender_pk: str, gas: int = 200_000) -> str:
    sender = web3.eth.account.from_key(sender_pk).address
    nonce  = get_next_nonce(sender)
    fees   = get_eip1559_fees()
    
    txn = fn_call.build_transaction({
        "chainId": CHAIN_ID,
        "gas":     gas,
        "nonce":   nonce,
        **fees,
    })
    signed  = web3.eth.account.sign_transaction(txn, private_key=sender_pk)
    tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = wait_with_retry(tx_hash, timeout=180)
    
    if receipt.status != 1:
        raise Exception("Giao dịch bị Revert bởi Smart Contract (Có thể do thiếu số dư)")
        
    hex_h = web3.to_hex(tx_hash)
    print(f"  ✅ TX OK — Hash: {hex_h}  Block: {receipt.blockNumber}")
    return hex_h

def send_eth(to: str, value_eth: float) -> str:
    """Gửi ETH từ Ví Tổng để trả phí Gas cho Ví Ẩn"""
    nonce = get_next_nonce(MASTER_ADDRESS)
    fees  = get_eip1559_fees()
    
    txn = {
        "nonce":   nonce,
        "to":      to,
        "value":   web3.to_wei(value_eth, "ether"),
        "gas":     21_000,
        "chainId": CHAIN_ID,
        **fees,
    }
    signed  = web3.eth.account.sign_transaction(txn, private_key=MASTER_PK)
    tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
    wait_with_retry(tx_hash, timeout=180)
    return web3.to_hex(tx_hash)

# ── Schemas ───────────────────────────────────────────────────
class TopupRequest(BaseModel):
    email:      str
    vnd_amount: int

class BuyRequest(BaseModel):
    email:       str
    orderId:     str
    jpyc_amount: int

class BalanceRequest(BaseModel):
    email: str

# ============================================================
#  API 1: NẠP TIỀN — Tạo Ví Ẩn & bơm JPYC (giả lập nhận fiat)
# ============================================================
@app.post("/api/topup")
async def topup_wallet(req: TopupRequest):
    print(f"\n💰 TOP-UP | Email: {req.email} | Số tiền: {req.vnd_amount:,} VND")

    if not web3.is_connected():
        raise HTTPException(status_code=503, detail="Không kết nối được Hardhat Node")

    # Bước 1: Tạo Ví Ẩn nếu khách chưa có
    if req.email not in user_db:
        new_acc = web3.eth.account.create()
        user_db[req.email] = {
            "address":      new_acc.address,
            "pk":           web3.to_hex(new_acc.key),
            "balance_jpyc": 0,
        }
        print(f"  🔑 Tạo Ví Ẩn mới: {new_acc.address}")
    if not web3.is_connected():
        raise HTTPException(status_code=503, detail="Không kết nối được Hardhat Node")

    if req.email not in user_db:
        raise HTTPException(404, "User not found. Need to check balance first to auto-create wallet.")
    
    # Số JPYC tự quy đổi
    RATE = 500000 / 3000
    jpyc_amount = int(req.vnd_amount / RATE)
    user = user_db[req.email]
    
    print(f"\n[TOP-UP] Email: {req.email} | Nhận: {req.vnd_amount} VND -> Quy đổi: {jpyc_amount} JPYC")
    
    try:
        # Pre-flight check: Kiểm tra Quỹ của Master có đủ JPYC không
        admin_balance = jpyc_contract.functions.balanceOf(MASTER_ADDRESS).call()
        required_wei = web3.to_wei(jpyc_amount, 'ether')
        
        if admin_balance < required_wei:
            raise Exception("Quỹ Admin đã cạn kiệt JPYC! Vui lòng liên hệ Admin nạp thêm.")
            
        # Chuyển (transfer) từ Quỹ của Master -> User
        transfer_abi = jpyc_contract.functions.transfer(user["address"], required_wei)
        tx_hash = send_tx(transfer_abi, MASTER_PK)
        
        user["balance_jpyc"] += jpyc_amount
        return {
            "status": "success",
            "jpyc_received": jpyc_amount,
            "new_balance": user["balance_jpyc"],
            "invisible_wallet": user["address"],
            "txHash": tx_hash
        }
    except Exception as e:
        print("Lỗi Topup:", e)
        return {"status": "error", "detail": str(e)}

class AdminMintRequest(BaseModel):
    amount: int

@app.post("/api/admin/mint")
async def admin_mint_jpyc(req: AdminMintRequest):
    if not web3.is_connected():
        raise HTTPException(status_code=503, detail="Không kết nối được Hardhat Node")
    try:
        print(f"\n[ADMIN] Đang đúc thêm {req.amount} JPYC vào Quỹ Dự Trữ...")
        mint_abi = jpyc_contract.functions.mint(MASTER_ADDRESS, web3.to_wei(req.amount, 'ether'))
        tx_hash = send_tx(mint_abi, MASTER_PK)
        return {"status": "success", "txHash": tx_hash}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# ============================================================
#  API 2: MUA SIM — Ví Ẩn ký giao dịch & gọi Smart Contract
# ============================================================
@app.post("/api/buy-sim")
async def buy_sim(req: BuyRequest):
    print(f"\n🛒 BUY SIM | Email: {req.email} | Order: {req.orderId} | {req.jpyc_amount} JPYC")

    if req.email not in user_db:
        raise HTTPException(status_code=400, detail="Không tìm thấy tài khoản. Vui lòng nạp tiền trước!")

    user = user_db[req.email]

    if user["balance_jpyc"] < req.jpyc_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Số dư không đủ. Hiện có {user['balance_jpyc']} JPYC, cần {req.jpyc_amount} JPYC"
        )

    amount_wei = web3.to_wei(req.jpyc_amount, "ether")
    user_addr  = Web3.to_checksum_address(user["address"])
    user_pk    = user["pk"]

    # Bước 1: PayMaster — Ví Tổng bơm ETH vào Ví Ẩn để trả phí Gas
    print(f"  ➡ [PayMaster] Bơm 0.01 ETH vào Ví Ẩn để trả Gas...")
    send_eth(user_addr, 0.01)

    # Bước 2: Ví Ẩn Approve JPYC cho AlooSimPayment
    print(f"  ➡ [Invisible Wallet] Approve {req.jpyc_amount} JPYC cho Smart Contract...")
    send_tx(
        jpyc_contract.functions.approve(
            Web3.to_checksum_address(CONTRACT_ADDRESS), amount_wei
        ),
        user_pk,
        gas=150_000
    )

    # Bước 3: Ví Ẩn gọi payForSim
    print(f"  ➡ [Invisible Wallet] Gọi payForSim('{req.orderId}', {req.jpyc_amount})...")
    pay_hash = send_tx(
        aloo_contract.functions.payForSim(req.orderId, amount_wei),
        user_pk,
        gas=250_000
    )

    user["balance_jpyc"] -= req.jpyc_amount
    print(f"  ✅ Mua SIM thành công! Số dư còn lại: {user['balance_jpyc']} JPYC")

    return {
        "status":      "success",
        "txHash":      pay_hash,
        "remaining":   user["balance_jpyc"],
        "orderId":     req.orderId,
        "message":     f"SIM đã cấp phát cho {req.email}",
    }

# ============================================================
#  API 3: XEM SỐ DƯ
# ============================================================
@app.post("/api/balance")
async def get_balance(req: BalanceRequest):
    if req.email not in user_db:
        # Tự động tạo Ví Ẩn ngay khi có email mới query số dư
        new_acc = web3.eth.account.create()
        user_db[req.email] = {
            "address":      new_acc.address,
            "pk":           web3.to_hex(new_acc.key),
            "balance_jpyc": 0,
        }
        print(f"  🔑 Auto-tạo Ví Ẩn cho {req.email}: {new_acc.address}")
        
    user = user_db[req.email]
    return {
        "balance": user["balance_jpyc"],
        "address": user["address"]
    }



# ============================================================
#  API 3: ADMIN RÚT DOANH THU (OFF-RAMP PIPELINE)
# ============================================================
@app.post("/api/admin/withdraw")
async def withdraw_revenue():
    if not web3.is_connected():
        raise HTTPException(status_code=503, detail="Không kết nối được Hardhat Node")
    try:
        print("\n[ADMIN - CHỐT CA] Đang gom toàn bộ doanh thu JPYC từ Két sắt Smart Contract...")
        
        # 1. KIỂM TRA SỐ DƯ KÉT SẮT
        contract_balance = jpyc_contract.functions.balanceOf(CONTRACT_ADDRESS).call()
        if contract_balance == 0:
            raise Exception("Két sắt đang trống, không có doanh thu để rút!")

        # 2. THỰC HIỆN RÚT TOÀN BỘ SỐ DƯ
        nonce = get_next_nonce(MASTER_ADDRESS)
        fees  = get_eip1559_fees()
        
        # CHÚ Ý: Truyền contract_balance vào hàm withdraw
        tx = aloo_contract.functions.withdraw(contract_balance).build_transaction({
            'chainId': 11155111, # Sepolia
            'gas': 100_000,
            'nonce': nonce,
            **fees,
        })
        
        # Ký và gửi transaction
        signed_tx = web3.eth.account.sign_transaction(tx, MASTER_PK)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        # Đợi transaction được xác nhận
        receipt = wait_with_retry(tx_hash, timeout=180)
        if receipt.status != 1:
            raise Exception("Lệnh Rút Doanh Thu bị Revert bởi mạng Blockchain!")
            
        print("🟢 GOM QUỸ THÀNH CÔNG!")
        return {
            "status": "success", 
            "message": "Đã rút toàn bộ doanh thu về Ví Tổng thành công!", 
            "txHash": web3.to_hex(tx_hash)
        }
    except Exception as e:
        print("🔴 Lỗi Rút Doanh Thu:", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Aloo SIM Invisible Wallet API v2.0 ✅", "connected": web3.is_connected()}
