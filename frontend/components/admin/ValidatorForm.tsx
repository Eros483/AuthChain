"use client";

import { useState, useEffect } from "react";

const API = "https://authchaingo.onrender.com/api";

function randomValidatorId() {
  return "val_" + crypto.randomUUID().slice(0, 8);
}

function randomPublicKey() {
  return (
    "0x" +
    Array.from(crypto.getRandomValues(new Uint8Array(32)))
      .map(b => b.toString(16).padStart(2, "0"))
      .join("")
  );
}

export default function ValidatorForm() {
  const [id, setId] = useState("");
  const [name, setName] = useState("");
  const [key, setKey] = useState("");

  useEffect(() => {
    setId(randomValidatorId());
    setKey(randomPublicKey());
  }, []);

  const submit = async () => {
    await fetch(`${API}/validators`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        id,
        name,
        public_key: key,
      }),
    });

    setId(randomValidatorId());
    setName("");
    setKey(randomPublicKey());
  };

  return (
    <div className="bg-[#121826] p-6 rounded-lg border border-white/10">
      <h3 className="text-lg mb-4 text-white">Add Validator</h3>

      <input
        className="w-full mb-3 px-3 py-2 bg-black/40 border border-white/10 rounded text-white placeholder:text-[#9BA3B4]"
        placeholder="validator id"
        value={id}
        onChange={e => setId(e.target.value)}
      />

      <input
        className="w-full mb-3 px-3 py-2 bg-black/40 border border-white/10 rounded text-white placeholder:text-[#9BA3B4]"
        placeholder="validator name"
        value={name}
        onChange={e => setName(e.target.value)}
      />

      <input
        className="w-full mb-4 px-3 py-2 bg-black/40 border border-white/10 rounded text-white placeholder:text-[#9BA3B4]"
        placeholder="public key"
        value={key}
        onChange={e => setKey(e.target.value)}
      />

      <button
        onClick={submit}
        className="bg-[#4DA3FF] text-black px-4 py-2 rounded"
      >
        Register Validator
      </button>
    </div>
  );
}
