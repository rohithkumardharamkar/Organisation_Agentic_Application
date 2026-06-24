import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Check, X } from 'lucide-react';

const ManagerApprovals: React.FC = () => {
  const [pendingItems, setPendingItems] = useState({ timesheets: [], leaves: [] });
  const [loading, setLoading] = useState(true);

  // Hardcode manager_id = 1 for demo purposes
  const managerId = 1;

  const fetchPending = async () => {
    try {
      setLoading(true);
      const resp = await fetch(`http://localhost:8000/api/v1/timesheets/pending/${managerId}`);
      if (resp.ok) {
        const data = await resp.json();
        setPendingItems(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPending();
  }, []);

  const handleAction = async (type: 'timesheet' | 'leave', id: number, action: 'Approved' | 'Rejected') => {
    try {
      const endpoint = type === 'timesheet' 
        ? `http://localhost:8000/api/v1/timesheets/${id}/approve`
        : `http://localhost:8000/api/v1/timesheets/leaves/${id}/approve`;
        
      const resp = await fetch(endpoint, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: action })
      });
      
      if (resp.ok) {
        alert(`${type} ${action} successfully`);
        fetchPending();
      }
    } catch (e) {
      alert("Failed to perform action");
    }
  };

  if (loading) return <div className="p-8">Loading pending approvals...</div>;

  return (
    <div className="p-8 space-y-8 bg-transparent min-h-screen text-slate-900 max-w-6xl mx-auto">
      <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
        Manager Approvals
      </h1>
      <p className="text-slate-500 text-lg mb-8">Review and approve employee timesheets and leaves.</p>

      <div className="grid grid-cols-1 gap-8">
        {/* Timesheets */}
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle className="text-slate-700">Pending Timesheets</CardTitle>
          </CardHeader>
          <CardContent>
            {pendingItems.timesheets.length === 0 ? (
              <p className="text-slate-500">No pending timesheets.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-500 bg-slate-50">
                      <th className="p-3">Employee ID</th>
                      <th className="p-3">Date</th>
                      <th className="p-3">Activity</th>
                      <th className="p-3">Hours</th>
                      <th className="p-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pendingItems.timesheets.map((ts: any) => (
                      <tr key={ts.timesheet_id} className="border-b border-slate-100 hover:bg-slate-50">
                        <td className="p-3 font-medium">EMP-{ts.employee_id}</td>
                        <td className="p-3">{ts.work_date}</td>
                        <td className="p-3">{ts.activity_type || 'N/A'}</td>
                        <td className="p-3">{ts.hours_logged}</td>
                        <td className="p-3 flex justify-end gap-2">
                          <button 
                            onClick={() => handleAction('timesheet', ts.timesheet_id, 'Approved')}
                            className="p-1.5 bg-emerald-100 text-emerald-600 rounded hover:bg-emerald-200 transition" title="Approve">
                            <Check className="w-4 h-4" />
                          </button>
                          <button 
                            onClick={() => handleAction('timesheet', ts.timesheet_id, 'Rejected')}
                            className="p-1.5 bg-red-100 text-red-600 rounded hover:bg-red-200 transition" title="Reject">
                            <X className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Leaves */}
        <Card className="bg-white border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle className="text-slate-700">Pending Leaves</CardTitle>
          </CardHeader>
          <CardContent>
            {pendingItems.leaves.length === 0 ? (
              <p className="text-slate-500">No pending leave requests.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-500 bg-slate-50">
                      <th className="p-3">Employee ID</th>
                      <th className="p-3">Type</th>
                      <th className="p-3">Start Date</th>
                      <th className="p-3">End Date</th>
                      <th className="p-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pendingItems.leaves.map((lv: any) => (
                      <tr key={lv.leave_id} className="border-b border-slate-100 hover:bg-slate-50">
                        <td className="p-3 font-medium">EMP-{lv.employee_id}</td>
                        <td className="p-3">{lv.leave_type}</td>
                        <td className="p-3">{lv.start_date}</td>
                        <td className="p-3">{lv.end_date}</td>
                        <td className="p-3 flex justify-end gap-2">
                          <button 
                            onClick={() => handleAction('leave', lv.leave_id, 'Approved')}
                            className="p-1.5 bg-emerald-100 text-emerald-600 rounded hover:bg-emerald-200 transition" title="Approve">
                            <Check className="w-4 h-4" />
                          </button>
                          <button 
                            onClick={() => handleAction('leave', lv.leave_id, 'Rejected')}
                            className="p-1.5 bg-red-100 text-red-600 rounded hover:bg-red-200 transition" title="Reject">
                            <X className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ManagerApprovals;
