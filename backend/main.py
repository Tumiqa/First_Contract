from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from web3 import Web3
from eth_account import Account
import secrets
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cấu Hình Blockchain (Mạng Sepolia Testnet)
RPC_URL = "https://eth-sepolia.g.alchemy.com/v2/grgjw1ZoCe7BqANEH_DS3"
web3 = Web3(Web3.HTTPProvider(RPC_URL))

# Ví Tổng (Master Wallet) - trả tiền Gas và nắm giữ JPYC
MASTER_PK = "cdb6004d0092b4c975f9171b9d9d3ae178e7bcfc7f4b7198eece11dd905cbbec"
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
    }
]

jpyc_contract = web3.eth.contract(
    address=Web3.to_checksum_address(TOKEN_ADDRESS), abi=ERC20_ABI)
aloo_contract = web3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=ALOO_ABI)

# ── "Database" in-memory (thực tế dùng PostgreSQL/MySQL) ─────
# { email: {address, pk, balance_jpyc} }
user_db: dict = {}

# ── Helpers ───────────────────────────────────────────────────
def send_tx(fn_call, sender_pk: str, gas: int = 200_000) -> str:
    sender = web3.eth.account.from_key(sender_pk).address
    nonce  = web3.eth.get_transaction_count(sender, "pending")
    txn    = fn_call.build_transaction({
        "chainId":  CHAIN_ID,
        "gas":      gas,
        "gasPrice": web3.eth.gas_price,
        "nonce":    nonce,
    })
    signed  = web3.eth.account.sign_transaction(txn, private_key=sender_pk)
    tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    hex_h   = web3.to_hex(tx_hash)
    print(f"  ✅ TX OK — Hash: {hex_h}  Block: {receipt.blockNumber}")
    return hex_h

def send_eth(to: str, value_eth: float) -> str:
    """Gửi ETH từ Ví Tổng để trả phí Gas cho Ví Ẩn"""
    nonce  = web3.eth.get_transaction_count(MASTER_ADDRESS, "pending")
    txn    = {
        "nonce":    nonce,
        "to":       to,
        "value":    web3.to_wei(value_eth, "ether"),
        "gas":      21_000,
        "gasPrice": web3.eth.gas_price,
        "chainId":  31337,
    }
    signed  = web3.eth.account.sign_transaction(txn, private_key=MASTER_PK)
    tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
    web3.eth.wait_for_transaction_receipt(tx_hash)
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

    user      = user_db[req.email]
    # Quy đổi VND → JPYC: 500,000 VND = 3,000 JPYC
    jpyc_mint = round(req.vnd_amount * 3000 / 500_000)
    amount_wei = web3.to_wei(jpyc_mint, "ether")

    # Bước 2: Mint JPYC vào Ví Tổng (Aloo nhận fiat, lập tức đúc token tương đương)
    print(f"  ➡ Mint {jpyc_mint} JPYC vào Ví Tổng (giả lập nhận tiền ngân hàng)...")
    send_tx(jpyc_contract.functions.mint(MASTER_ADDRESS, amount_wei), MASTER_PK)

    # Bước 3: Chuyển JPYC từ Quỹ Aloo → Ví Ẩn của khách
    print(f"  ➡ Transfer {jpyc_mint} JPYC từ Quỹ → Ví Ẩn khách...")
    topup_hash = send_tx(
        jpyc_contract.functions.transfer(
            Web3.to_checksum_address(user["address"]), amount_wei
        ),
        MASTER_PK
    )

    user["balance_jpyc"] += jpyc_mint
    print(f"  ✅ Nạp xong! Số dư Ví Ẩn: {user['balance_jpyc']} JPYC")

    return {
        "status":           "success",
        "jpyc_received":    jpyc_mint,
        "new_balance":      user["balance_jpyc"],
        "invisible_wallet": user["address"],
        "txHash":           topup_hash,
    }

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
        return {"balance": 0, "address": None}
    user = user_db[req.email]
    return {
        "balance": user["balance_jpyc"],
        "address": user["address"]
    }

# ── Compat: Webhook (giữ cho MetaMask frontend cũ) ──────────
@app.post("/webhook/blockchain")
async def blockchain_webhook(payload: dict):
    print(f"\n🔔 Webhook | Order: {payload.get('orderId')} | TxHash: {payload.get('txHash')}")
    return {"status": "received"}

@app.get("/")
async def root():
    return {"message": "Aloo SIM Invisible Wallet API v2.0 ✅", "connected": web3.is_connected()}
