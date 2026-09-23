import { useEffect, useState } from "react";
import { api } from "../api/client";
type R = { id: number; store_id: number; label: string; length_cm: number; buffer_cm: number };
export default function RailsPage() {
  const [rows, setRows] = useState<R[]>([]);
  const [drafts, setDrafts] = useState<Record<number, string>>({});
  const [msg, setMsg] = useState(""); const [err, setErr] = useState("");
  useEffect(() => {
    api<R[]>("/rails").then(rs => {
      setRows(rs);
      setDrafts(Object.fromEntries(rs.map(r => [r.id, String(r.buffer_cm)])));
    });
  }, []);
  async function save(r: R) {
    setMsg(""); setErr("");
    const buffer_cm = Number(drafts[r.id]);
    if (!Number.isFinite(buffer_cm) || buffer_cm < 0) { setErr("缓冲须为不小于 0 的数字"); return; }
    try {
      const updated = await api<R>(`/rails/${r.id}/buffer`, { method: "PATCH", body: JSON.stringify({ buffer_cm }) });
      setRows(rows.map(x => x.id === r.id ? updated : x));
      setDrafts(d => ({ ...d, [r.id]: String(updated.buffer_cm) }));
      setMsg(`${r.label} 缓冲已保存为 ${updated.buffer_cm}cm`);
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
  }
  return (<>
    <h2>挂杆</h2>
    {msg && <div className="ok">{msg}</div>}
    {err && <div className="err">{err}</div>}
    <table className="table"><thead><tr><th>标签</th><th>门店</th><th>长度 cm</th><th>间隔缓冲 cm</th><th></th></tr></thead>
    <tbody>{rows.map(r => <tr key={r.id}><td>{r.label}</td><td>{r.store_id}</td><td className="mono">{r.length_cm}</td>
      <td><input className="buffer-input" type="number" min={0} step={1}
        value={drafts[r.id] ?? ""} onChange={e => setDrafts(d => ({ ...d, [r.id]: e.target.value }))} /></td>
      <td><button onClick={() => save(r)}>保存缓冲</button></td>
    </tr>)}</tbody></table>
    <p className="muted-tip">缓冲为相邻衣物间的最小留白；上杆时缓冲计入占用，取件释放后空隙按缓冲规则重新可入。</p>
  </>);
}
