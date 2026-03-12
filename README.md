# 📱 Aloo E-SIM — Hệ thống Thanh toán Web3 (Web2.5 Invisible Wallet)

> Đồ án phân tích thiết kế Fintech: Tích hợp Smart Contract Ethereum (Mạng Sepolia) vào quy trình thanh toán SIM Quốc Tế. 
> Dự án sử dụng kiến trúc **Invisible Wallet (Ví Ẩn)** và **Custodial Relayer** để mang lại trải nghiệm mượt mà như Web2 (Thẻ Visa, MoMo, VietQR) cho người dùng cuối, trong khi mọi bút toán và lưu trữ tài sản đều được thực thi & minh bạch 100% trên Blockchain.

![Aloo E-SIM Banner](https://img.shields.io/badge/Fintech-Blockchain-blue) ![Sepolia](https://img.shields.io/badge/Network-Sepolia-purple) ![License](https://img.shields.io/badge/License-MIT-green)

---

## 🌟 Tính năng nổi bật

1. **Web2.5 UX (Trải nghiệm người dùng 2 chiều):**
   - Khách hàng có thể nạp tiền bằng VNĐ, hệ thống tự động quy đổi và giao dịch bằng đồng JPYC (Mock Stablecoin) trên Blockchain.
   - Giao diện Dark-mode cao cấp với hiệu ứng Glassmorphism.
2. **Invisible Wallet (Ví Ẩn tự động):**
   - Chỉ cần nhập Email, hệ thống `backend` tự động khởi tạo và gán một địa chỉ Ví Web3 duy nhất cho khách hàng. Không cần cài đặt ví MetaMask phức tạp.
3. **Mô hình Custodial Relayer (Quỹ dự trữ Paymaster):**
   - Phí Gas (ETH) được hệ thống (Master Wallet) tài trợ ẩn dưới nền. Hệ thống Admin có thể tự đúc (Mint) thêm JPYC vào Quỹ.
4. **Minh bạch On-chain:**
   - Mọi giao dịch Mua SIM, Nạp Quỹ đều có TxHash để tra cứu công khai trực tiếp trên [Sepolia Etherscan](https://sepolia.etherscan.io/).

---

## 🛠 Cấu trúc thư mục

```text
First_Contract/
├── contracts/
│   ├── AlooSimPayment.sol   # Smart Contract: Mua SIM, nhận thanh toán
│   └── MockERC20.sol        # Smart Contract: Token JPYC giả lập
├── backend/
│   ├── main.py              # Server FastAPI: Xử lý Ví Ẩn, Web3.py, Relayer
│   └── requirements.txt     # Thư viện Python
├── scripts/
│   └── deploy.js            # Script deploy Smart Contracts lên Sepolia
├── admin.html               # Frontend quản trị (React-like CDN + ethers.js)
├── index.html               # Frontend người dùng (Giao diện Web2.5)
├── hardhat.config.ts        # Cấu hình mạng Hardhat & Sepolia
└── .env.example             # (Bạn cần tạo mô hình file .env từ file này)
```

---

## 🚀 Hướng dẫn cài đặt & Chạy dự án từ đầu

Bất kỳ ai cũng có thể `fork/clone` dự án này về và chạy thành công trên máy tính bằng cách làm theo tuần tự các bước dưới đây.

### Yêu cầu tiên quyết 
- **Node.js**: Phiên bản >= 18.x
- **Python**: Phiên bản >= 3.10
- Tài khoản [Alchemy](https://www.alchemy.com/) (Để lấy API RPC URL miễn phí)
- Ví Metamask có chứa một ít **Sepolia ETH** (Nhận miễn phí tại [Sepolia Faucet](https://sepoliafaucet.com/)).

### Bước 1: Clone dự án và cài đặt
```bash
git clone https://github.com/Tumiqa/First_Contract.git
cd First_Contract

# Cài đặt thư viện Node.js (Hardhat, Ethers, viem...)
npm install
```

### Bước 2: Cài đặt biến môi trường `.env`
Tạo một file có tên là `.env` ngay tại thư mục gốc `First_Contract/` và điền thông tin ví Sepolia (Master Wallet) của bạn:

```env
# URL API từ Alchemy kết nối mạng Sepolia
SEPOLIA_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/YOUR_ALCHEMY_API_KEY_HERE

# Private Key của Ví MetaMask làm Master Wallet (CÓ SẴN SEPOLIA ETH ĐỂ TRẢ PHÍ GAS)
# (KHÔNG để lộ file này lên Github)
SEPOLIA_PRIVATE_KEY=0x_YOUR_PRIVATE_KEY_HERE
```

### Bước 3: Deploy Smart Contracts lên mạng Sepolia (Tùy chọn)
Nếu bạn muốn dùng hợp đồng của riêng mình, hãy chạy lệnh sau để Deploy:
```bash
npx hardhat run scripts/deploy.js --network sepolia
```
_Lưu ý: Sau khi lệnh chạy xong, Terminal sẽ in ra 2 địa chỉ của `MockERC20` và `AlooSimPayment`. Bạn hãy lưu lại 2 địa chỉ này._

### Bước 4: Cập nhật địa chỉ Hợp đồng mới (Nếu bạn tự Deploy)
1. Mở file `backend/main.py`:
   - Thay `TOKEN_ADDRESS` thành địa chỉ JPYC mới.
   - Thay `CONTRACT_ADDRESS` thành địa chỉ AlooSimPayment mới.
2. Mở file `admin.html`:
   - Thay `MASTER_WALLET` thành địa chỉ ví MetaMask của bạn (Khớp với Private Key trong `.env`).
   - Thay `JPYC_ADDRESS` thành địa chỉ JPYC mới.

_*(Nếu bạn không tự Deploy, hệ thống đã cấu hình sẵn hợp đồng công khai của dự án).*_

### Bước 5: Chạy Backend Server
Mở một Terminal mới để chạy Python Backend. Chúng ta dùng `FastAPI` để làm Relayer.
```bash
cd backend

# (Khuyên dùng) Tạo môi trường ảo (Virtual Environment)
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Cài đặt thư viện
pip install -r requirements.txt

# Khởi chạy Backend Server ở cổng 8000
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Server chạy thành công khi có dòng chữ: `Uvicorn running on http://0.0.0.0:8000`

### Bước 6: Chạy Frontend (UI Người dùng & Admin)
Mở một Terminal mới (hoặc dùng VSCode Live Server):
```bash
# Ở thư mục gốc First_Contract/
python -m http.server 5500
```
Truy cập trình duyệt:
- **Trang Khách hàng (Mua SIM):** `http://localhost:5500/index.html`
- **Trang Quản trị (Kế toán Quỹ):** `http://localhost:5500/admin.html`

---

## 🎮 Hướng dẫn Kịch bản Demo

Kịch bản thao tác này giúp bạn phô diễn toàn bộ điểm mạnh của dự án trước hội đồng giám khảo:

1. **Chuẩn bị Quỹ (Vai trò Admin):**
   - Mở trang `admin.html`. Đây là "Ví Tổng" (Master Wallet - Paymaster).
   - Nhập số `100000` và nhấn **Đúc (Mint) JPYC**. 
   - Hệ thống mô phỏng công ty nạp tiền pháp định vào tài khoản thế chấp và đúc JPYC tương ứng. 
   - Click vào "Xem TxHash" để chứng minh giao dịch Blockchain là **Có Thật**.

2. **Khách hàng nạp tiền (Vai trò User):**
   - Mở trang `index.html`.
   - Gõ một địa chỉ thẻ Email mới (ví dụ: `giam_khao@gmail.com`) rồi click chuột ra ngoài. Hệ thống **tự động phân bổ Ví Web3** cho giám khảo ngay dưới ô email.
   - Ở cột bên trái, khách chọn nạp `1,000,000 đ`. Bộ tính toán tự động hiển thị nhận được `~6000 JPYC`.
   - Bấm Thanh toán qua MoMo/QR. Backend API sẽ tự động lấy JPYC từ Quỹ của Master và chuyển sang "Ví Ẩn" của khách hàng. Phí Gas hoàn toàn do Hệ thống chịu!

3. **Khách hàng Mua SIM:**
   - Số dư của khách hiện tại là VNĐ (và JPYC tương ứng).
   - Chọn "SIM Nhật 15 Ngày" với giá VNĐ (được ghim quy đổi JPYC). 
   - Nhấn thanh toán. Backend sẽ đưa "Ví Ẩn" ký giao dịch gọi Smart Contract `payForSim()`.
   - Bấm vào TxHash trong hộp Log để xác nhận trên Etherscan. Doanh thu đã được ghi nhận trên Smart Contract!

4. **Kiểm tra chéo:**
   - Quay lại trang `admin.html`, ấn "Cập nhật số dư". Bạn sẽ thấy Quỹ Tổng (Master Wallet) đã **BỊ TRỪ** đi đúng lượng JPYC mà khách đã nạp, phản ánh tính khép kín của dòng tiền Tài Chính Kế Toán.

---

## 💻 Tech Stack Sử Dụng

- **Smart Contract:** Solidity `0.8.28`, Hardhat.
- **Backend / Relayer:** Python 3, `FastAPI`, `Web3.py`, `uvicorn`.
- **Frontend:** Vanilla HTML/CSS/JS thuần, kiến trúc giao diện Web 2.5 `Glassmorphism`, tương tác qua API và `ethers.js v6`.

---
*Developed with ❤️ as a University FinTech Thesis Demonstration.*
