// src/pages/LandingPage.jsx
import React from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 relative overflow-hidden">
      {/* Animated gradient background */}
      <div className="absolute inset-0 -z-10 glass-bg" />

      {/* Floating blobs */}
      <motion.div
        className="blob blob-1"
        animate={{ x: [0, -40, 0], y: [0, -20, 0] }}
        transition={{ repeat: Infinity, duration: 8, ease: "easeInOut" }}
      />
      <motion.div
        className="blob blob-2"
        animate={{ x: [0, 40, 0], y: [0, 20, 0] }}
        transition={{ repeat: Infinity, duration: 10, ease: "easeInOut" }}
      />

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-3xl text-center p-12"
      >
        <h1 className="text-5xl md:text-6xl font-extrabold text-slate-900 drop-shadow-sm leading-tight">
          Invoice & PO Matching Tool
        </h1>

        <p className="mt-6 text-lg md:text-xl text-slate-700 max-w-2xl mx-auto">
          Automatically compare invoices and purchase orders to find discrepancies
          — faster and smarter. Upload your files and get a clear, actionable
          result.
        </p>

        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          onClick={() => navigate("/matcher")}
          className="mt-10 inline-flex items-center gap-3 bg-white/30 backdrop-blur-md border border-white/20 hover:bg-white/40 text-slate-900 font-semibold px-8 py-3 rounded-xl shadow-lg"
        >
          Get Started
        </motion.button>

        <p className="mt-8 text-sm text-slate-500">Secure • Fast • Simple</p>
      </motion.div>
    </div>
  );
}
