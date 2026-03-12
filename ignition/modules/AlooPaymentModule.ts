import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";
import { parseUnits } from "viem";

export default buildModule("AlooPaymentModule", (m) => {
  // 1. Get deployer account parameter (defaults to the first account if not specified)
  const deployer = m.getAccount(0);

  // 2. Deploy Mock Token
  const token = m.contract("MockERC20", ["Mock JPYC", "JPYC"]);

  // 3. Deploy Aloo Payment Contract 
  const paymentContract = m.contract("AlooSimPayment", [token]);

  // 4. Mint 1,000,000 JPYC to Master Wallet
  const amt = parseUnits("1000000", 18);
  m.call(token, "mint", [deployer, amt]);

  return { token, paymentContract };
});
