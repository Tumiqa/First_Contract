// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract AlooSimPayment is Ownable {
    IERC20 public acceptedToken; // Token được chấp nhận (VD: JPYC hoặc USDC)

    enum OrderStatus { None, Paid, Refunded, Completed }

    struct Order {
        address customer;
        uint256 amount;
        OrderStatus status;
    }

    // Mapping từ mã đơn hàng (mã chuỗi hoặc hash) sang thông tin đơn
    mapping(string => Order) public orders;

    // Các sự kiện để phục vụ Audit và bắn Webhook
    event PaymentReceived(string orderId, address indexed customer, uint256 amount);
    event RefundIssued(string orderId, address indexed customer, uint256 amount);
    event FundsWithdrawn(address indexed owner, uint256 amount);

    constructor(address _tokenAddress) Ownable(msg.sender) {
        acceptedToken = IERC20(_tokenAddress);
    }

    // 1. Hàm thanh toán (Khách hàng gọi)
    function payForSim(string memory _orderId, uint256 _amount) external {
        require(orders[_orderId].status == OrderStatus.None, "Order already exists");
        require(_amount > 0, "Amount must be greater than 0");

        // Chuyển JPYC/USDC từ ví khách hàng vào Smart Contract
        // Lưu ý: Khách hàng cần gọi hàm approve() trên token contract trước đó
        require(acceptedToken.transferFrom(msg.sender, address(this), _amount), "Transfer failed");

        orders[_orderId] = Order({
            customer: msg.sender,
            amount: _amount,
            status: OrderStatus.Paid
        });

        emit PaymentReceived(_orderId, msg.sender, _amount);
    }

    // 2. Hàm hoàn tiền (Admin/Hệ thống Aloo gọi khi SIM lỗi)
    function refund(string memory _orderId) external onlyOwner {
        Order storage order = orders[_orderId];
        require(order.status == OrderStatus.Paid, "Order is not in Paid status");

        order.status = OrderStatus.Refunded;
        
        // Trả lại tiền cho khách hàng
        require(acceptedToken.transfer(order.customer, order.amount), "Refund transfer failed");

        emit RefundIssued(_orderId, order.customer, order.amount);
    }

    // 3. Hàm đánh dấu hoàn tất (Admin gọi định kỳ để chốt doanh thu)
    function completeOrder(string memory _orderId) external onlyOwner {
        require(orders[_orderId].status == OrderStatus.Paid, "Order not paid");
        orders[_orderId].status = OrderStatus.Completed;
    }

    // 4. Hàm rút doanh thu về ví công ty
    function withdraw(uint256 _amount) external onlyOwner {
        require(acceptedToken.balanceOf(address(this)) >= _amount, "Insufficient balance");
        require(acceptedToken.transfer(owner(), _amount), "Withdraw failed");
        emit FundsWithdrawn(owner(), _amount);
    }
}