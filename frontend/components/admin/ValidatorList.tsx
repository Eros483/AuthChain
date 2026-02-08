"use client";

import { useEffect, useState } from "react";

const API = "https://authchaingo.onrender.com/api";

interface Validator {
  id: string;
  name: string;
  active: boolean;
}

export default function ValidatorList() {
  const [validators, setValidators] = useState<Validator[]>([]);

  const load = async () => {
    const res = await fetch(`${API}/validators`);
    const data = await res.json();
    setValidators(data.validators || []);
  };

  const remove = async (id: string) => {
    await fetch(`${API}/validators/${id}`, { method: "DELETE" });
    load();
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="bg-[#121826] p-6 rounded-lg border border-white/10">
      <h3 className="text-lg mb-4">Active Validators</h3>

      <ul className="space-y-3">
        {validators.map(v => (
          <li
            key={v.id}
            className="flex items-center justify-between border border-white/10 px-3 py-2 rounded"
          >
            <div>
              <div className="font-medium">{v.name}</div>
              <div className="text-xs text-[#9BA3B4]">{v.id}</div>
            </div>

            <button
              onClick={() => remove(v.id)}
              className="text-red-400 text-sm"
            >
              Remove
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
