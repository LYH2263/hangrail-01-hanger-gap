import { Fragment, useEffect, useState } from "react";
import { api } from "../api/client";
type Rail = { id: number; label: string; length_cm: number; buffer_cm: number };
type Seg = { ticket_code: string; garment_name: string; start_cm: number; end_cm: number };
type Occ = { rail_id: number; label: string; length_cm: number; buffer_cm: number; segments: Seg[] };
export default function OccupancyPage() {
  const [rails, setRails] = useState<Rail[]>([]);
  const [maps, setMaps] = useState<Occ[]>([]);
  useEffect(() => {
    api<Rail[]>("/rails").then(async rs => {
      setRails(rs);
      const all = await Promise.all(rs.map(r => api<Occ>(`/occupancy/${r.id}`)));
      setMaps(all);
    });
  }, []);
  return (<>
    <h2>占位图（横向尺线）</h2>
    {maps.map(m => (
      <div className="ruler-wrap" key={m.rail_id}>
        <div className="ruler-label">
          <span>{m.label}</span>
          <span className="mono">0 — {m.length_cm} cm · 相邻间隔缓冲 {m.buffer_cm ?? 0} cm</span>
        </div>
        <div className="ruler">
          {m.segments.map((s, i) => {
            const next = m.segments[i + 1];
            const gap = next ? next.start_cm - s.end_cm : 0;
            return (
              <Fragment key={i}>
                <div className="seg" style={{ left: `${(s.start_cm / m.length_cm) * 100}%`, width: `${((s.end_cm - s.start_cm) / m.length_cm) * 100}%` }}
                  title={`${s.ticket_code} ${s.start_cm}-${s.end_cm}cm`}>
                  {s.garment_name}
                </div>
                {next && gap > 0.001 && (
                  <div className={`seg-gap${gap / m.length_cm < 0.05 ? " seg-gap--tight" : ""}`}
                    style={{ left: `${(s.end_cm / m.length_cm) * 100}%`, width: `${(gap / m.length_cm) * 100}%` }}
                    title={`相邻留白 ${gap} cm（缓冲 ${m.buffer_cm ?? 0} cm）`}>
                    <span className="seg-gap-mark">{gap}cm</span>
                  </div>
                )}
              </Fragment>
            );
          })}
        </div>
      </div>
    ))}
    {!rails.length && <p>暂无挂杆</p>}
  </>);
}
