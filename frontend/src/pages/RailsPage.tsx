import { useEffect, useState } from "react";
import { api } from "../api/client";
type R = { id: number; store_id: number; label: string; length_cm: number; buffer_cm: number };
export default function RailsPage() {
  const [rows, setRows] = useState<R[]>([]);
  const [drafts, setDrafts] = useState<Record<number, string>>({});
  const [savingId, setSavingId] = useState<number | null>(null);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  const reload = () =>
    api<R[]>("/rails").then((rs) => {
      setRows(rs);
      setDrafts(Object.fromEntries(rs.map((r) => [r.id, String(r.buffer_cm ?? 0)])));
    });
  useEffect(() => {
    reload();
  }, []);

  async function save(r: R) {
    setMsg(""); setErr("");
    const value = Number(drafts[r.id]);
    if (!Number.isFinite(value) || value < 0) {
      setErr(`${r.label}：缓冲须为不小于 0 的数字`);
      return;
    }
    setSavingId(r.id);
    try {
      await api(`/rails/${r.id}`, { method: "PATCH", body: JSON.stringify({ buffer_cm: value }) });
      setMsg(`${r.label} 缓冲已保存为 ${value} cm`);
      await reload();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setSavingId(null);
    }
  }

  return (<>
    <h2>挂杆</h2>
    <p style={{ color: "var(--hang-muted)", fontSize: ".85rem", marginTop: "-.4rem" }}>
      缓冲为相邻已挂衣物之间必须留出的最小间隔（cm），计入占用；杆的两端不加缓冲，0 表示可贴边连续挂满。
    </p>
    {msg && <div className="ok">{msg}</div>}
    {err && <div className="err">{err}</div>}
    <table className="table">
      <thead><tr><th>标签</th><th>门店</th><th>长度 cm</th><th>缓冲 cm</th><th></th></tr></thead>
      <tbody>{rows.map(r => (
        <tr key={r.id}>
          <td>{r.label}</td>
          <td>{r.store_id}</td>
          <td className="mono">{r.length_cm}</td>
          <td>
            <input
              type="number" min={0} step={1} style={{ width: 90 }}
              value={drafts[r.id] ?? String(r.buffer_cm ?? 0)}
              onChange={(e) => setDrafts((d) => ({ ...d, [r.id]: e.target.value }))}
            />
          </td>
          <td>
            <button disabled={savingId === r.id} onClick={() => save(r)}>
              {savingId === r.id ? "保存中…" : "保存"}
            </button>
          </td>
        </tr>
      ))}</tbody>
    </table>
  </>);
}
