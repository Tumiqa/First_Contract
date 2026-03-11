import { network } from "hardhat";
import { parseUnits } from "viem";

async function main() {
  const { viem } = await network.connect();
  const [deployer, customer] = await viem.getWalletClients();
  console.log(
    "Deploying contracts with the account:",
    deployer.account.address,
  );

  // 1. Deploy Mock Token (Giả lập JPYC)
  const token = await viem.deployContract("MockERC20", ["Mock JPYC", "JPYC"]);
  console.log("Mock JPYC deployed to:", token.address);

  // 2. Deploy Aloo Payment Contract
  const paymentContract = await viem.deployContract("AlooSimPayment", [
    token.address,
  ]);
  console.log("AlooSimPayment deployed to:", paymentContract.address);

  // 3. Tặng 10,000 JPYC cho khách hàng để test
  await token.write.mint([customer.account.address, parseUnits("10000", 18)]);
  console.log("Minted 10000 JPYC cho ví khách hàng:", customer.account.address);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
