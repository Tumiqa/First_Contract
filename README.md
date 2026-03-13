# 📱 Aloo E-SIM — Hệ thống Thanh toán Web3 (Web2.5 Invisible Wallet)

> Đồ án phân tích thiết kế Fintech: Tích hợp Smart Contract Ethereum (Mạng Sepolia) vào quy trình thanh toán SIM Quốc Tế. 
> Dự án sử dụng kiến trúc **Invisible Wallet (Ví Ẩn)** và **Custodial Relayer** để mang lại trải nghiệm mượt mà như Web2 (Thẻ Visa, PayPal, Apple Pay, VietQR) cho người dùng cuối, trong khi mọi bút toán và lưu trữ tài sản đều được thực thi & minh bạch 100% trên Blockchain.

![Aloo E-SIM Banner](https://img.shields.io/badge/Fintech-Blockchain-blue) ![Sepolia](https://img.shields.io/badge/Network-Sepolia-purple) ![License](https://img.shields.io/badge/License-MIT-green)

---

## 🌟 Tính năng nổi bật

1. **Cổng Thanh Toán Đa Quốc Gia (Multi-Currency Support):**
   - Hỗ trợ thanh toán linh hoạt bằng **VNĐ, JPY, USD, EUR, CNY**.
   - **Địa phương hóa phương thức thanh toán**: Tự động hiển thị các phương thức quen thuộc như PayPal/Apple Pay (US/EU), PayPay/LINE Pay (Nhật), Alipay/WeChat Pay (Trung Quốc), VietQR/MoMo (Việt Nam).
   - Hệ thống tự động quy đổi tỷ giá thời gian thực sang đồng JPYC (Stablecoin) trên Blockchain.

2. **Invisible Wallet (Ví Ẩn tự động):**
   - Chỉ cần nhập Email, hệ thống `backend` tự động khởi tạo và quản lý một địa chỉ Ví Web3 duy nhất cho khách hàng. Không cần cài đặt ví MetaMask phức tạp.

3. **Mô hình Custodial Relayer (Quỹ dự trữ Paymaster):**
   - Phí Gas (ETH) được hệ thống (Master Wallet) tài trợ ẩn dưới nền. Hệ thống Admin có quyền kiểm soát toàn diện: Đúc (Mint) thêm JPYC hoặc Rút doanh thu (Withdraw) về ví công ty.

4. **Trang Quản Trị Hệ Thống Chuyên Nghiệp (Enterprise Admin UI):**
   - Giao diện quản lý dòng tiền, số dư Blockchain, và thực hiện chốt ca (Off-ramp) với thuật ngữ chuẩn kế toán/tài chính.
   - Theo dõi số dư ETH (Phí gas) và JPYC (Doanh thu) trong thời gian thực.

5. **Minh bạch On-chain:**
   - Mọi giao dịch Mua SIM, Nạp Quỹ đều có TxHash để tra cứu công khai trực tiếp trên [Sepolia Etherscan](https://sepolia.etherscan.io/).

---

## 🛠 Cấu trúc thư mục

```text
First_Contract/
├── contracts/
│   ├── AlooSimPayment.sol   # Smart Contract: Mua SIM, nhận thanh toán & Rút tiền
│   └── MockERC20.sol        # Smart Contract: Token JPYC (Stablecoin giả lập)
├── backend/
│   ├── main.py              # Server FastAPI: Điều phối Ví Ẩn, Web3.py Logic, Relayer API
│   └── requirements.txt     # Danh sách thư viện Python (web3, fastapi, uvicorn...)
├── scripts/
│   └── deploy.js            # Script khởi tạo (Deploy) Smart Contracts lên mạng Sepolia
├── admin.html               # Trang Quản trị: Kiểm soát quỹ và Rút doanh thu
├── index.html               # Trang Khách hàng: Cổng thanh toán đa quốc gia & Mua SIM
├── hardhat.config.ts        # Cấu hình môi trường Blockchain (Sepolia Testnet)
└── .env                     # Biến môi trường (RPC URL, Master Private Key)
```

---

## 🚀 Hướng dẫn cài đặt & Chạy dự án

### Yêu cầu tiên quyết 
- **Node.js**: >= 18.x
- **Python**: >= 3.10
- **Alchemy API Key**: Kết nối tới mạng Sepolia
- Ví Metamask có chứa một ít **Sepolia ETH** để làm Master Wallet.

### Bước 1: Cài đặt thư viện
```bash
npm install
```

### Bước 2: Cấu hình môi trường
Tạo file `.env` tại thư mục gốc:
```env
SEPOLIA_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/KEY_CUA_BAN
SEPOLIA_PRIVATE_KEY=0x_KEY_VÍ_CỦA_BẠN
```

### Bước 3: Chạy Backend (Relayer Server)
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Bước 4: Chạy Frontend
Bạn có thể mở trực tiếp `index.html` và `admin.html` bằng trình duyệt hoặc dùng Live Server trong VS Code (Port 5500).
- URL local: `http://localhost:5500/index.html`

---

## 🎮 Kịch bản Demo Hội Đồng

1. **Khởi tạo & Nạp quỹ (Admin):**
   - Truy cập `admin.html`, kiểm tra số dư Master Wallet.
   - Thực hiện **Mint JPYC** để bơm "vốn" cho hệ thống.

2. **Trải nghiệm Đa quốc gia (User):**
   - Truy cập `index.html`, chuyển đổi giữa các vùng **🇺🇸 USD, 🇯🇵 JPY, 🇨🇳 CNY**.
   - Quan sát phương thức thanh toán tự động thay đổi (Alipay -> PayPal).
   - Nhập Email khachhang@demo.com -> Hệ thống tự tạo ví Ẩn.

3. **Mua SIM & Ghi nhận Blockchain:**
   - Chọn gói **SIM Nhật 15 Ngày** (Đã bao gồm Data + Nghe gọi + Số điện thoại thực).
   - Nhấn thanh toán. Quan sát Log hệ thống thực hiện ký giao dịch On-chain ngầm.
   - Kiểm tra mã giao dịch (TxHash) trên Etherscan.

4. **Chốt doanh thu:**
   - Quay lại `admin.html`, bấm **RÚT DOANH THU VỀ VÍ CÔNG TY** để gom tiền từ Smart Contract về tài khoản kế toán chính.

---

## 💻 Tech Stack
- **Web3 Interface**: `ethers.js v6` (Frontend), `web3.py v6` (Backend).
- **Relayer Core**: `FastAPI` (Python).
- **Smart Contracts**: Solidity `0.8.28`, OpenZeppelin Standards.
- **UI Architecture**: Web2.5 Responsive Design, CSS Glassmorphism.

---
*Phát triển bởi ❤️ - Dự án Fintech Blockchain Demonstration.*
