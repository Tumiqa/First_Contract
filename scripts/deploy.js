import { network } from "hardhat";
import { parseUnits } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import "dotenv/config";

async function main() {
  const { viem } = await network.connect();
  
  // Create account directly from Private Key to avoid testnet injection issues
  const pk = process.env.SEPOLIA_PRIVATE_KEY || "";
  const deployerAccount = privateKeyToAccount(pk.startsWith("0x") ? pk : `0x${pk}`);
  
  console.log("Deploying contracts with the account:", deployerAccount.address);

  // 1. Deploy Mock Token
  console.log("Deploying Mock JPYC...");
  const token = await viem.deployContract("MockERC20", ["Mock JPYC", "JPYC"], { account: deployerAccount });
  console.log("Mock JPYC deployed to:", token.address);

  // 2. Deploy Aloo Payment Contract
  console.log("Deploying AlooSimPayment...");
  const paymentContract = await viem.deployContract("AlooSimPayment", [token.address], { account: deployerAccount });
  console.log("AlooSimPayment deployed to:", paymentContract.address);

  // 3. Mint 1,000,000 JPYC to Master Wallet
  console.log("Minting JPYC...");
  await token.write.mint([deployerAccount.address, parseUnits("1000000", 18)], { account: deployerAccount });
  console.log("Minted 1,000,000 JPYC (Quỹ Aloo) vào Ví Tổng:", deployerAccount.address);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
