// src/pages/MatcherPage.jsx
import React, { useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import ResultCard from "../components/ResultCard";

export default function MatcherPage() {
  const [invoiceFile, setInvoiceFile] = useState(null);
  const [poFile, setPoFile] = useState(null);
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleFileChange = (e, setter) => setter(e.target.files[0]);

  const handleRunMatching = async () => {
    if (!invoiceFile || !poFile) {
      setError("Please upload both an invoice and a purchase order.");
      return;
    }
    setError("");
    setIsLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append("invoice", invoiceFile);
    formData.append("po", poFile);

    try {
      const response = await axios.post(
        "https://invoice-po-matcher-vtq4.onrender.com/match",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      setResult(response.data);
    } catch (err) {
      setError("An error occurred. Is the backend server running?");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      {/* Header */}
      <div className="max-w-6xl mx-auto px-6">
        <button onClick={() => navigate("/")} className="text-blue-600 mb-6">
          ← Back
        </button>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
          className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start"
        >
          {/* Left: Upload / Action panel (glass) */}
          <div className="lg:col-span-2">
            <div className="backdrop-blur-md bg-white/40 border border-white/30 rounded-2xl p-8 shadow-2xl">
              <h2 className="text-3xl font-bold text-slate-900 mb-2">
                Invoice & PO Matching
              </h2>
              <p className="text-slate-600 mb-6">
                Upload your documents below to check for mismatches.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <label className="block">
                  <span className="text-sm font-medium text-slate-700 mb-2 inline-flex items-center gap-2">
                    📄 Upload Invoice
                  </span>
                  <div className="relative">
                    <input
                      type="file"
                      onChange={(e) => handleFileChange(e, setInvoiceFile)}
                      className="opacity-0 absolute inset-0 w-full h-full cursor-pointer"
                    />
                    <div className="border border-dashed border-white/30 rounded-xl px-4 py-6 flex items-center gap-4 bg-white/20">
                      <button className="px-4 py-2 rounded-full bg-white/60 text-blue-700 font-semibold shadow-sm">
                        Choose File
                      </button>
                      <div className="text-sm text-slate-700">
                        {invoiceFile ? invoiceFile.name : "No file chosen"}
                      </div>
                    </div>
                  </div>
                </label>

                <label className="block">
                  <span className="text-sm font-medium text-slate-700 mb-2 inline-flex items-center gap-2">
                    📋 Upload Purchase Order
                  </span>
                  <div className="relative">
                    <input
                      type="file"
                      onChange={(e) => handleFileChange(e, setPoFile)}
                      className="opacity-0 absolute inset-0 w-full h-full cursor-pointer"
                    />
                    <div className="border border-dashed border-white/30 rounded-xl px-4 py-6 flex items-center gap-4 bg-white/20">
                      <button className="px-4 py-2 rounded-full bg-white/60 text-blue-700 font-semibold shadow-sm">
                        Choose File
                      </button>
                      <div className="text-sm text-slate-700">
                        {poFile ? poFile.name : "No file chosen"}
                      </div>
                    </div>
                  </div>
                </label>
              </div>

              <div className="flex gap-4 items-center">
                <button
                  onClick={handleRunMatching}
                  disabled={isLoading}
                  className="flex-1 bg-blue-600 text-white font-bold py-3 px-6 rounded-xl shadow-lg hover:bg-blue-700 disabled:opacity-60"
                >
                  {isLoading ? "Processing..." : "Run Matching"}
                </button>

                <button
                  onClick={() => {
                    setInvoiceFile(null);
                    setPoFile(null);
                    setResult(null);
                    setError("");
                  }}
                  className="px-4 py-3 rounded-xl bg-white/40 border border-white/20"
                >
                  Reset
                </button>
              </div>

              {error && <p className="mt-4 text-red-500">{error}</p>}
            </div>
          </div>

          {/* Right: Results summary (spacious) */}
          <div>
            <div className="rounded-2xl p-6 h-full">
              {!result && (
                <div className="backdrop-blur-md bg-white/30 border border-white/20 rounded-xl p-6 text-slate-600">
                  <h3 className="text-lg font-semibold mb-2">Preview</h3>
                  <p className="text-sm">
                    After you run matching, a clean summary will appear here —
                    status, vendor match, totals, and any issues with clear
                    callouts.
                  </p>
                </div>
              )}

              {result && <ResultCard data={result} />}
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
