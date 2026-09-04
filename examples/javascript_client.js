// JavaScript SDK example — TextShield v2.2
const BASE = "http://127.0.0.1:8000";

async function analyze(text) {
  const res = await fetch(`${BASE}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  console.log(await res.json());
}

analyze("You've won a prize! Visit http://bit.ly/abc");
