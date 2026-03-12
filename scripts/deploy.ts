import { createWalletClient, createPublicClient, http, parseUnits } from "viem";
import { sepolia } from "viem/chains";
import { privateKeyToAccount } from "viem/accounts";
import "dotenv/config";

// Read Hardhat compiled artifacts directly
import mockTokenArtifact from "../artifacts/contracts/MockERC20.sol/MockERC20.json" assert { type: "json" };
import paymentArtifact from "../artifacts/contracts/AlooSimPayment.sol/AlooSimPayment.json" assert { type: "json" };

async function main() {
  const pk = process.env.SEPOLIA_PRIVATE_KEY;
  if (!pk) throw new Error("SEPOLIA_PRIVATE_KEY missing");
  const rpc = process.env.SEPOLIA_RPC_URL;
  if (!rpc) throw new Error("SEPOLIA_RPC_URL missing");

  const account = privateKeyToAccount(pk.startsWith("0x") ? pk : `0x${pk}`);

  const publicClient = createPublicClient({
    chain: sepolia,
    transport: http(rpc),
  });

  const walletClient = createWalletClient({
    account,
    chain: sepolia,
    transport: http(rpc),
  });

  console.log("Deploying contracts with the account:", account.address);
  const balance = await publicClient.getBalance({ address: account.address });
  console.log("Sepolia ETH Balance:", balance.toString());

  // 1. Deploy Mock Token
  console.log("Deploying MockERC20...");
  const mockTokenHash = await walletClient.deployContract({
    abi: mockTokenArtifact.abi,
    bytecode: mockTokenArtifact.bytecode as `0x${string}`,
    args: ["Mock JPYC", "JPYC"],
  });
  
  const mockTokenReceipt = await publicClient.waitForTransactionReceipt({ hash: mockTokenHash });
  const mockTokenAddress = mockTokenReceipt.contractAddress!;
  console.log("Mock JPYC deployed to:", mockTokenAddress);

  // 2. Deploy AlooSimPayment
  console.log("Deploying AlooSimPayment...");
  const paymentHash = await walletClient.deployContract({
    abi: paymentArtifact.abi,
    bytecode: paymentArtifact.bytecode as `0x${string}`,
    args: [mockTokenAddress],
  });
  
  const paymentReceipt = await publicClient.waitForTransactionReceipt({ hash: paymentHash });
  const paymentAddress = paymentReceipt.contractAddress!;
  console.log("AlooSimPayment deployed to:", paymentAddress);

  // 3. Mint 1,000,000 JPYC to Master Wallet
  console.log("Minting 1,000,000 JPYC to Master Wallet...");
  const mintHash = await walletClient.writeContract({
    address: mockTokenAddress,
    abi: mockTokenArtifact.abi,
    functionName: "mint",
    args: [account.address, parseUnits("1000000", 18)],
  });
  await publicClient.waitForTransactionReceipt({ hash: mintHash });
  console.log("MintTx complete. Hash:", mintHash);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
