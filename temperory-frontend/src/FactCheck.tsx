import React, { useState } from "react";

// Define the expected structure of the API response


const FactCheck: React.FC = () => {
  const [inputText, setInputText] = useState<string>("");
  const [result, setResult] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  const handleFactCheck = async () => {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch("http://localhost:8000/fact/check/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text: inputText }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.message || "An error occurred.");
      } else {
        setResult(data.res );
      }
    } catch (err) {
      setError("Network or server error.");
    }

    setLoading(false);
  };

  return (
    <div style={{ maxWidth: 600, margin: "0 auto", padding: "2rem" }}>
      <h2>🕵️‍♂️ Fact Check Assistant</h2>
      <textarea
        rows={6}
        style={{ width: "100%", padding: "1rem", marginBottom: "1rem" }}
        placeholder="Paste a WhatsApp message or claim here..."
        value={inputText}
        onChange={(e) => setInputText(e.target.value)}
      />
      <button onClick={handleFactCheck} disabled={loading}>
        {loading ? "Checking..." : "Check Fact"}
      </button>

      {error && <p style={{ color: "red", marginTop: "1rem" }}>{error}</p>}

      {result && (
        <div style={{ marginTop: "1rem", background: "#000000", padding: "1rem" }}>
          <p><strong>Confidence Score:</strong> {result[0][1]} / 10</p>
          <p><strong>Comments:</strong> {result[1][1]}</p>
        </div>
      )}
    </div>
  );
};

export default FactCheck;
