"use client";

import { useWallet, useConnection } from "@solana/wallet-adapter-react";
import { AnchorProvider, Program } from "@coral-xyz/anchor";
import { PublicKey } from "@solana/web3.js";
import idl from "@/idl/authchain_lock.json";

export default function ApproveButton({ execution }: { execution: string }) {
  const { publicKey, signTransaction, signAllTransactions } = useWallet();
  const { connection } = useConnection();

  const approve = async () => {
    if (!publicKey || !signTransaction || !signAllTransactions) {
      throw new Error("Wallet does not support signing");
    }

    const provider = new AnchorProvider(
      connection,
      { publicKey, signTransaction, signAllTransactions },
      AnchorProvider.defaultOptions()
    );

    const program = new Program(idl as any, provider);

    await program.methods
      .approve()
      .accounts({
        execution: new PublicKey(execution),
        validator: publicKey,
      })
      .rpc();
  };

  return (
    <button onClick={approve} className="bg-green-500 px-4 py-2 rounded">
      Approve on Solana
    </button>
  );
}
