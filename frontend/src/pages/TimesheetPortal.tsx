import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  Clock, Plus, Send, CheckCircle, XCircle, AlertCircle,
  Calendar, BarChart3, FileText, Trash2, TrendingUp
} from 'lucide-react';

const API = 'http://localhost:8000/api/v1/timesheets';

const ACTIVITY_TYPES = ['Development', 'Code Review', 'Testing / QA', 'Design', 'Meeting', 'Documentation', 'Research', 'DevOps', 'Support', 'Training'];
const LEAVE_TYPES = ['Sick', 'Vacation', 'Personal', 'Casual', 'Compensatory'];
const STATUS_COLORS: Record<string, string> = {
  Approved: 'bg-emerald-100 text-emerald-700',
  Pending: 'bg-amber-100 text-amber-700',
  Rejected: 'bg-red-100 text-red-700',
};

const badge = (status: string) => (
  <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${STATUS_COLORS[status] || 'bg-slate-100 text-slate-600'}`}>
    {status === 'Approved' && <CheckCircle className="w-3 h-3" />}
    {status === 'Pending' && <AlertCircle className="w-3 h-3" />}
    {status === 'Rejected' && <XCircle className="w-3 h-3" />}
    {status}
  </span>
);

export default function TimesheetPortal() {
  const { userEmail } = useAuth();
  const [tab, setTab] = useState<'log' | 'history' | 'leave' | 'analytics'>('log');
  const [projects, setProjects] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [leaves, setLeaves] = useState<any[]>([]);
  const [leaveBalance, setLeaveBalance] = useState<any[]>([]);
  const [toast, setToast] = useState('');
  const empId = 1; // demo

  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(''), 3000); };

  const loadProjects = async () => {
    const r = await fetch(`${API}/projects/list`); setProjects(await r.json());
  };
  const loadStats = async () => {
    const r = await fetch(`${API}/employee/${empId}/stats`); setStats(await r.json());
  };
  const loadHistory = async () => {
    const r = await fetch(`${API}/employee/${empId}`); setHistory(await r.json());
  };
  const loadLeaves = async () => {
    const [l, b] = await Promise.all([
      fetch(`${API}/leaves/employee/${empId}`).then(r => r.json()),
      fetch(`${API}/leaves/employee/${empId}/balance`).then(r => r.json()),
    ]);
    setLeaves(l); setLeaveBalance(b.balance || []);
  };

  useEffect(() => { loadProjects(); loadStats(); }, []);
  useEffect(() => { if (tab === 'history') loadHistory(); }, [tab]);
  useEffect(() => { if (tab === 'leave') loadLeaves(); }, [tab]);
  useEffect(() => { if (tab === 'analytics') loadStats(); }, [tab]);

  // ── Log Tab ────────────────────────────────────────────────────────────────
  const today = new Date().toISOString().split('T')[0];
  const [rows, setRows] = useState([{ project_id: '', work_date: today, hours_logged: '', activity_type: '', note: '' }]);
  const totalHours = rows.reduce((s, r) => s + (parseFloat(r.hours_logged) || 0), 0);

  const addRow = () => setRows(r => [...r, { project_id: '', work_date: today, hours_logged: '', activity_type: '', note: '' }]);
  const removeRow = (i: number) => setRows(r => r.filter((_, idx) => idx !== i));
  const updateRow = (i: number, k: string, v: string) => setRows(r => r.map((row, idx) => idx === i ? { ...row, [k]: v } : row));

  const submitAll = async () => {
    const valid = rows.filter(r => r.project_id && r.work_date && parseFloat(r.hours_logged) > 0);
    if (!valid.length) { showToast('Fill at least one complete row.'); return; }
    const res = await fetch(`${API}/bulk`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ employee_id: empId, entries: valid.map(r => ({ ...r, hours_logged: parseFloat(r.hours_logged) })) }),
    });
    if (res.ok) { showToast(`✅ ${valid.length} entries submitted for approval!`); setRows([{ project_id: '', work_date: today, hours_logged: '', activity_type: '', note: '' }]); loadStats(); }
    else showToast('❌ Submission failed.');
  };

  const deleteEntry = async (id: number) => {
    await fetch(`${API}/${id}`, { method: 'DELETE' });
    showToast('Entry deleted.'); loadHistory(); loadStats();
  };

  // ── Leave Tab ──────────────────────────────────────────────────────────────
  const [leaveForm, setLeaveForm] = useState({ leave_type: 'Vacation', start_date: today, end_date: today, reason: '' });
  const submitLeave = async () => {
    const res = await fetch(`${API}/leaves`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ employee_id: empId, ...leaveForm }),
    });
    if (res.ok) { showToast('✅ Leave submitted!'); loadLeaves(); }
    else { const e = await res.json(); showToast(`❌ ${e.detail || 'Error'}`); }
  };

  const TAB_BTN = (id: typeof tab, label: string, Icon: any) => (
    <button onClick={() => setTab(id)} className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition ${tab === id ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-600 hover:bg-slate-100'}`}>
      <Icon className="w-4 h-4" />{label}
    </button>
  );

  return (
    <div className="min-h-screen bg-slate-50 p-6 space-y-6">
      {toast && <div className="fixed top-4 right-4 z-50 bg-slate-900 text-white px-5 py-3 rounded-xl shadow-2xl text-sm font-semibold animate-fade-in">{toast}</div>}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black tracking-tight bg-gradient-to-r from-indigo-600 via-blue-600 to-emerald-500 bg-clip-text text-transparent flex items-center gap-3">
            <Clock className="w-8 h-8 text-indigo-600" /> Timesheet & Leave Management
          </h1>
          <p className="text-slate-500 mt-1 text-sm">Log hours, track approvals, manage leave — all in one place</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-slate-400">Logged in as</p>
          <p className="text-sm font-bold text-slate-700">{userEmail}</p>
        </div>
      </div>

      {/* Stats Bar */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'This Week', value: `${stats.week_hours}h`, sub: `Target: 40h`, color: stats.week_hours >= 40 ? 'text-emerald-600' : 'text-amber-600' },
            { label: 'This Month', value: `${stats.month_hours}h`, sub: 'Hours logged', color: 'text-indigo-600' },
            { label: 'Pending', value: stats.pending_count, sub: 'Awaiting approval', color: 'text-amber-600' },
            { label: 'Compliance', value: `${stats.compliance_rate}%`, sub: 'Weekly target', color: stats.compliance_rate >= 90 ? 'text-emerald-600' : 'text-red-600' },
          ].map(s => (
            <div key={s.label} className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm">
              <p className="text-xs text-slate-400 font-medium uppercase tracking-wide">{s.label}</p>
              <p className={`text-2xl font-black mt-1 ${s.color}`}>{s.value}</p>
              <p className="text-xs text-slate-500 mt-0.5">{s.sub}</p>
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 bg-white border border-slate-200 rounded-2xl p-2 shadow-sm">
        {TAB_BTN('log', 'Log Hours', Plus)}
        {TAB_BTN('history', 'My History', FileText)}
        {TAB_BTN('leave', 'Leave Management', Calendar)}
        {TAB_BTN('analytics', 'Analytics', BarChart3)}
      </div>

      {/* ── LOG HOURS ── */}
      {tab === 'log' && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <h2 className="font-bold text-slate-800">Time Entries</h2>
            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-500">Total: <span className="font-black text-slate-900">{totalHours.toFixed(1)}h</span></span>
              <button onClick={addRow} className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition">
                <Plus className="w-3.5 h-3.5" /> Add Row
              </button>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wide">
                <tr>
                  <th className="px-4 py-3 text-left">Project</th>
                  <th className="px-4 py-3 text-left w-36">Date</th>
                  <th className="px-4 py-3 text-left w-24">Hours</th>
                  <th className="px-4 py-3 text-left">Activity</th>
                  <th className="px-4 py-3 text-left">Notes</th>
                  <th className="px-4 py-3 w-10"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {rows.map((row, i) => (
                  <tr key={i} className="hover:bg-slate-50">
                    <td className="px-4 py-2">
                      <select value={row.project_id} onChange={e => updateRow(i, 'project_id', e.target.value)} className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-xs focus:ring-1 focus:ring-indigo-500 focus:outline-none">
                        <option value="">Select project…</option>
                        {projects.map(p => <option key={p.project_id} value={p.project_id}>{p.project_name}</option>)}
                      </select>
                    </td>
                    <td className="px-4 py-2">
                      <input type="date" value={row.work_date} onChange={e => updateRow(i, 'work_date', e.target.value)} className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-xs focus:ring-1 focus:ring-indigo-500 focus:outline-none" />
                    </td>
                    <td className="px-4 py-2">
                      <input type="number" value={row.hours_logged} onChange={e => updateRow(i, 'hours_logged', e.target.value)} step="0.5" min="0" max="24" placeholder="0.0" className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-xs font-bold focus:ring-1 focus:ring-indigo-500 focus:outline-none" />
                    </td>
                    <td className="px-4 py-2">
                      <select value={row.activity_type} onChange={e => updateRow(i, 'activity_type', e.target.value)} className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-xs focus:ring-1 focus:ring-indigo-500 focus:outline-none">
                        <option value="">Select…</option>
                        {ACTIVITY_TYPES.map(a => <option key={a}>{a}</option>)}
                      </select>
                    </td>
                    <td className="px-4 py-2">
                      <input type="text" value={row.note} onChange={e => updateRow(i, 'note', e.target.value)} placeholder="Brief description…" className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-xs focus:ring-1 focus:ring-indigo-500 focus:outline-none" />
                    </td>
                    <td className="px-4 py-2">
                      {rows.length > 1 && <button onClick={() => removeRow(i)} className="text-slate-300 hover:text-red-500 transition"><Trash2 className="w-3.5 h-3.5" /></button>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-6 py-4 border-t border-slate-100 flex justify-end">
            <button onClick={submitAll} className="flex items-center gap-2 px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-bold transition shadow-md shadow-indigo-200">
              <Send className="w-4 h-4" /> Submit for Approval
            </button>
          </div>
        </div>
      )}

      {/* ── HISTORY ── */}
      {tab === 'history' && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="font-bold text-slate-800">My Timesheet History</h2>
            <p className="text-xs text-slate-400 mt-0.5">{history.length} entries found</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wide">
                <tr>
                  <th className="px-4 py-3 text-left">Date</th>
                  <th className="px-4 py-3 text-left">Project</th>
                  <th className="px-4 py-3 text-left">Activity</th>
                  <th className="px-4 py-3 text-center">Hours</th>
                  <th className="px-4 py-3 text-center">Status</th>
                  <th className="px-4 py-3 text-left">Notes</th>
                  <th className="px-4 py-3 w-10"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {history.slice(0, 50).map((ts: any) => (
                  <tr key={ts.timesheet_id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 text-slate-600 font-medium">{ts.work_date}</td>
                    <td className="px-4 py-3 text-slate-800 font-semibold max-w-[160px] truncate">{ts.project_name}</td>
                    <td className="px-4 py-3 text-slate-600">{ts.activity_type || '—'}</td>
                    <td className="px-4 py-3 text-center font-black text-indigo-600">{ts.hours_logged}h</td>
                    <td className="px-4 py-3 text-center">{badge(ts.approval_status)}</td>
                    <td className="px-4 py-3 text-slate-500 text-xs max-w-[180px] truncate">{ts.note || '—'}</td>
                    <td className="px-4 py-3">
                      {ts.approval_status !== 'Approved' && (
                        <button onClick={() => deleteEntry(ts.timesheet_id)} className="text-slate-300 hover:text-red-500 transition"><Trash2 className="w-3.5 h-3.5" /></button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!history.length && <div className="py-16 text-center text-slate-400 text-sm">No timesheet entries found.</div>}
          </div>
        </div>
      )}

      {/* ── LEAVE ── */}
      {tab === 'leave' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Apply Leave */}
          <div className="lg:col-span-1 bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
            <h2 className="font-bold text-slate-800 flex items-center gap-2"><Calendar className="w-4 h-4 text-indigo-600" />Apply for Leave</h2>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-1.5 block">Leave Type</label>
                <select value={leaveForm.leave_type} onChange={e => setLeaveForm(f => ({ ...f, leave_type: e.target.value }))} className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                  {LEAVE_TYPES.map(t => <option key={t}>{t}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-1.5 block">From</label>
                  <input type="date" value={leaveForm.start_date} onChange={e => setLeaveForm(f => ({ ...f, start_date: e.target.value }))} className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none" />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-1.5 block">To</label>
                  <input type="date" value={leaveForm.end_date} onChange={e => setLeaveForm(f => ({ ...f, end_date: e.target.value }))} className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none" />
                </div>
              </div>
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-1.5 block">Reason</label>
                <textarea value={leaveForm.reason} onChange={e => setLeaveForm(f => ({ ...f, reason: e.target.value }))} rows={3} placeholder="Optional reason…" className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm resize-none focus:ring-2 focus:ring-indigo-500 focus:outline-none" />
              </div>
              <button onClick={submitLeave} className="w-full flex items-center justify-center gap-2 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-bold transition">
                <Send className="w-4 h-4" /> Submit Leave Request
              </button>
            </div>

            {/* Balance */}
            {leaveBalance.length > 0 && (
              <div className="pt-4 border-t border-slate-100 space-y-2">
                <p className="text-xs font-bold text-slate-500 uppercase tracking-wide">Annual Balance</p>
                {leaveBalance.map((b: any) => (
                  <div key={b.leave_type} className="flex items-center gap-2">
                    <span className="text-xs text-slate-600 w-24 font-medium">{b.leave_type}</span>
                    <div className="flex-1 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                      <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${b.percentage_used}%` }} />
                    </div>
                    <span className="text-xs font-bold text-slate-700 w-16 text-right">{b.remaining}/{b.annual_allowance}d left</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Leave History */}
          <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100">
              <h2 className="font-bold text-slate-800">Leave History</h2>
            </div>
            <div className="divide-y divide-slate-100">
              {leaves.map((lv: any) => (
                <div key={lv.leave_id} className="px-6 py-4 flex items-center justify-between hover:bg-slate-50">
                  <div>
                    <p className="font-semibold text-slate-800 text-sm">{lv.leave_type} Leave</p>
                    <p className="text-xs text-slate-500">{lv.start_date} → {lv.end_date} · {lv.days} day{lv.days !== 1 ? 's' : ''}</p>
                  </div>
                  {badge(lv.approval_status)}
                </div>
              ))}
              {!leaves.length && <div className="py-16 text-center text-slate-400 text-sm">No leave records found.</div>}
            </div>
          </div>
        </div>
      )}

      {/* ── ANALYTICS ── */}
      {tab === 'analytics' && stats && (
        <div className="space-y-6">
          {/* Daily Bar Chart */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
            <h2 className="font-bold text-slate-800 flex items-center gap-2 mb-4"><TrendingUp className="w-4 h-4 text-indigo-600" />Daily Hours — Last 7 Days</h2>
            <div className="flex items-end gap-3 h-32">
              {stats.daily_breakdown?.map((d: any) => {
                const pct = Math.min((d.hours / 10) * 100, 100);
                const label = new Date(d.date).toLocaleDateString('en', { weekday: 'short' });
                return (
                  <div key={d.date} className="flex-1 flex flex-col items-center gap-1">
                    <span className="text-xs font-bold text-slate-600">{d.hours > 0 ? `${d.hours}h` : ''}</span>
                    <div className="w-full bg-slate-100 rounded-t-lg overflow-hidden" style={{ height: '80px' }}>
                      <div className={`w-full rounded-t-lg transition-all ${d.hours >= 7 ? 'bg-emerald-500' : d.hours > 0 ? 'bg-indigo-500' : 'bg-slate-200'}`} style={{ height: `${pct}%`, marginTop: `${100 - pct}%` }} />
                    </div>
                    <span className="text-xs text-slate-400 font-medium">{label}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Hours by Project */}
          {stats.hours_by_project?.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <h2 className="font-bold text-slate-800 mb-4">Hours by Project — This Month</h2>
              <div className="space-y-3">
                {stats.hours_by_project.map((p: any) => {
                  const total = stats.hours_by_project.reduce((s: number, x: any) => s + x.hours, 0);
                  const pct = total > 0 ? Math.round((p.hours / total) * 100) : 0;
                  return (
                    <div key={p.project_id} className="flex items-center gap-3">
                      <span className="text-xs text-slate-600 font-medium w-48 truncate">{p.project_name}</span>
                      <div className="flex-1 bg-slate-100 rounded-full h-2 overflow-hidden">
                        <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${pct}%` }} />
                      </div>
                      <span className="text-xs font-bold text-slate-700 w-16 text-right">{p.hours}h ({pct}%)</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Summary Cards */}
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: 'Approved Entries', value: stats.approved_count, color: 'text-emerald-600', bg: 'bg-emerald-50' },
              { label: 'Pending Approval', value: stats.pending_count, color: 'text-amber-600', bg: 'bg-amber-50' },
              { label: 'Rejected Entries', value: stats.rejected_count, color: 'text-red-600', bg: 'bg-red-50' },
            ].map(c => (
              <div key={c.label} className={`${c.bg} rounded-2xl p-5 border border-slate-200`}>
                <p className="text-xs text-slate-500 font-medium uppercase tracking-wide">{c.label}</p>
                <p className={`text-3xl font-black mt-1 ${c.color}`}>{c.value}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
