# Aloo SIM — Hệ thống Thanh toán SIM Quốc Tế qua Blockchain (Web2.5)

> Đồ án Fintech: Tích hợp Smart Contract Ethereum vào quy trình thanh toán SIM du lịch, sử dụng kiến trúc **Invisible Wallet** để mang lại trải nghiệm Web2 cho người dùng cuối trong khi vẫn đảm bảo tính minh bạch trên Blockchain.

---

## Tổng quan kiến trúc

```
Khách hàng (Web2 UI)
      │ Email + Nạp tiền / Mua SIM
      ▼
Backend Python (FastAPI Relayer)
  ├── Tạo Ví Ẩn (Invisible Wallet) per user
  ├── PayMaster: trả phí Gas hộ khách
  └── Ký giao dịch với Ví Ẩn
      │
      ▼
Smart Contract (Solidity - Hardhat)
  ├── MockERC20.sol     → Token JPYC giả lập
  └── AlooSimPayment.sol → Nhận thanh toán & ghi nhận đơn hàng
```

### Luồng nghiệp vụ

```
[Thứ 7] Khách nạp 500,000 VND
   → Backend Mint JPYC → Transfer vào Ví Ẩn KH
   → Số dư hiện trên UI

[Thứ 5] Khách mua SIM Nhật 1,000 JPYC
   → Ví Ẩn Approve → payForSim() trên Smart Contract
   → TxHash ghi sổ kế toán Blockchain
```

---

## Cấu trúc dự án

```
First_Contract/
├── contracts/
│   ├── AlooSimPayment.sol   # Smart Contract chính
│   └── MockERC20.sol        # Token JPYC giả lập (ERC-20)
├── scripts/
│   └── deploy.js            # Deploy & mint JPYC vào Ví Tổng
├── backend/
│   ├── main.py              # FastAPI Relayer — Invisible Wallet logic
│   └── requirements.txt
├── frontend/
│   └── index.html           # Giao diện Ví điện tử (Web2.5 UI)
├── test/
│   └── Counter.ts
└── hardhat.config.ts
```

---

## Cài đặt & Chạy Demo

### Yêu cầu
- Node.js >= 18, Python >= 3.10
- MetaMask (tùy chọn, cho luồng Web3 trực tiếp)

### Bước 1: Cài dependencies

```bash
npm install
pip install -r backend/requirements.txt
```

### Bước 2: Khởi động Hardhat Node

```bash
npx hardhat node
```

### Bước 3: Deploy Smart Contract

```bash
npx hardhat run scripts/deploy.js --network localhost
```

> Sau deploy, copy địa chỉ `MockERC20` và `AlooSimPayment` → điền vào `backend/main.py` (dòng `TOKEN_ADDRESS`, `CONTRACT_ADDRESS`).

### Bước 4: Chạy Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Bước 5: Mở Frontend

```bash
python -m http.server 5500 --directory frontend
```

Truy cập: **http://localhost:5500**

---

## Demo Kịch bản bảo vệ đồ án

| Bước | Thao tác | Kết quả |
|------|----------|---------|
| 1 | Nhập email, bấm **Nạp 500k VND** | Backend tạo Ví Ẩn, bơm 3,000 JPYC |
| 2 | Bấm **Mua SIM (1,000 JPYC)** | Ví Ẩn ký giao dịch, trừ 1,000 JPYC |
| 3 | Xem Audit Log | TxHash Blockchain minh bạch |

> **Điểm nhấn:** Khách hàng không cần biết MetaMask hay crypto. Dòng tiền `Ví Ẩn KH → Smart Contract` hoàn toàn minh bạch, không thể bị kiểm toán bắt lỗi.

---

## Smart Contract API

### `AlooSimPayment.sol`

| Function | Caller | Mô tả |
|---|---|---|
| `payForSim(orderId, amount)` | Khách hàng / Ví Ẩn | Thanh toán mua SIM |
| `refund(orderId)` | Admin | Hoàn tiền nếu SIM lỗi |
| `completeOrder(orderId)` | Admin | Đánh dấu hoàn tất |
| `withdraw(amount)` | Admin | Rút doanh thu |

### Backend API

| Endpoint | Method | Mô tả |
|---|---|---|
| `/api/topup` | POST | Nạp tiền vào Ví Ẩn |
| `/api/buy-sim` | POST | Mua SIM từ Ví Ẩn |
| `/api/balance` | POST | Xem số dư |

---

## Công nghệ sử dụng

- **Solidity 0.8.28** + OpenZeppelin — Smart Contract
- **Hardhat 3** + Viem — Development framework
- **Python FastAPI** + web3.py — Backend Relayer
- **Vanilla HTML/CSS/JS** — Frontend (không cần framework)

---

*Đồ án Fintech — Aloo Telecom 2026*
