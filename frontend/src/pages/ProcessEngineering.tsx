import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '../components/ui/card';
import { Target, AlertTriangle, FileSearch, TrendingUp } from 'lucide-react';

const ProcessEngineering: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'submit' | 'view'>('submit');
  
  // Form State
  const [projectId, setProjectId] = useState('1'); // Default dummy project
  const [reportDate, setReportDate] = useState(new Date().toISOString().split('T')[0]);
  const [reportType, setReportType] = useState('Sprint');
  const [timeframeLabel, setTimeframeLabel] = useState('Sprint 42');
  const [achievements, setAchievements] = useState('');
  const [risks, setRisks] = useState('');
  const [missing, setMissing] = useState('');
  const [future, setFuture] = useState('');

  // View State
  const [reports, setReports] = useState<any[]>([]);
  const [filterType, setFilterType] = useState('');
  const [loading, setLoading] = useState(false);

  const employeeId = 1; // dummy engineer ID

  const fetchReports = async () => {
    try {
      setLoading(true);
      let url = `http://localhost:8000/api/v1/process/reports/${projectId}`;
      if (filterType) url += `?report_type=${filterType}`;
      
      const resp = await fetch(url);
      if (resp.ok) {
        const data = await resp.json();
        setReports(data.reports || []);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'view') {
      fetchReports();
    }
  }, [activeTab, projectId, filterType]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        project_id: parseInt(projectId),
        employee_id: employeeId,
        report_date: reportDate,
        report_type: reportType,
        timeframe_label: timeframeLabel,
        achievements,
        risks_identified: risks,
        missing_requirements: missing,
        future_improvements: future
      };

      const resp = await fetch("http://localhost:8000/api/v1/process/reports", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      
      if (resp.ok) {
        alert("Process Report successfully submitted!");
        setAchievements('');
        setRisks('');
        setMissing('');
        setFuture('');
      } else {
        alert("Failed to submit process report.");
      }
    } catch (e) {
      alert("Error connecting to API.");
    }
  };

  return (
    <div className="p-8 space-y-8 bg-transparent min-h-screen text-slate-900 max-w-6xl mx-auto">
      <div className="flex justify-between items-end border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-orange-600 to-amber-500 bg-clip-text text-transparent">
            Process Engineering
          </h1>
          <p className="text-slate-500 text-lg mt-2">Log sprint achievements, project risks, and track improvements.</p>
        </div>
        
        <div className="flex bg-slate-100 p-1 rounded-lg">
          <button 
            className={`px-4 py-2 rounded-md font-medium text-sm transition ${activeTab === 'submit' ? 'bg-white text-orange-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
            onClick={() => setActiveTab('submit')}
          >
            Submit Report
          </button>
          <button 
            className={`px-4 py-2 rounded-md font-medium text-sm transition ${activeTab === 'view' ? 'bg-white text-orange-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
            onClick={() => setActiveTab('view')}
          >
            View Reports
          </button>
        </div>
      </div>

      {activeTab === 'submit' && (
        <form onSubmit={handleSubmit} className="bg-white border border-slate-200 shadow-sm rounded-xl p-8 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">Project</label>
              <select value={projectId} onChange={e => setProjectId(e.target.value)} className="w-full border-slate-200 rounded-lg p-2.5 bg-slate-50 border focus:ring-2 focus:ring-orange-500 outline-none">
                <option value="1">Yottaflex AI Migration</option>
                <option value="2">Enterprise Dashboard V2</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">Report Type</label>
              <select value={reportType} onChange={e => setReportType(e.target.value)} className="w-full border-slate-200 rounded-lg p-2.5 bg-slate-50 border focus:ring-2 focus:ring-orange-500 outline-none">
                <option value="Daily">Daily</option>
                <option value="Weekly">Weekly</option>
                <option value="Sprint">Sprint</option>
                <option value="Monthly">Monthly</option>
                <option value="Yearly">Yearly</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">Date</label>
              <input type="date" value={reportDate} onChange={e => setReportDate(e.target.value)} className="w-full border-slate-200 rounded-lg p-2.5 bg-slate-50 border focus:ring-2 focus:ring-orange-500 outline-none" required />
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">Timeframe Label</label>
              <input type="text" placeholder="e.g. Sprint 42" value={timeframeLabel} onChange={e => setTimeframeLabel(e.target.value)} className="w-full border-slate-200 rounded-lg p-2.5 bg-slate-50 border focus:ring-2 focus:ring-orange-500 outline-none" required />
            </div>
          </div>

          <hr className="border-slate-100" />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <label className="flex items-center gap-2 text-sm font-bold text-emerald-700 mb-2"><Target className="w-4 h-4"/> Achievements</label>
              <textarea 
                rows={4} value={achievements} onChange={e => setAchievements(e.target.value)}
                className="w-full border-slate-200 rounded-lg p-4 bg-emerald-50/30 border focus:ring-2 focus:ring-emerald-500 outline-none placeholder:text-slate-400"
                placeholder="What was successfully completed in this timeframe?" required
              />
            </div>
            <div>
              <label className="flex items-center gap-2 text-sm font-bold text-red-700 mb-2"><AlertTriangle className="w-4 h-4"/> Risks Identified</label>
              <textarea 
                rows={4} value={risks} onChange={e => setRisks(e.target.value)}
                className="w-full border-slate-200 rounded-lg p-4 bg-red-50/30 border focus:ring-2 focus:ring-red-500 outline-none placeholder:text-slate-400"
                placeholder="What bottlenecks, delays, or issues arose?"
              />
            </div>
            <div>
              <label className="flex items-center gap-2 text-sm font-bold text-amber-700 mb-2"><FileSearch className="w-4 h-4"/> Missing Requirements</label>
              <textarea 
                rows={4} value={missing} onChange={e => setMissing(e.target.value)}
                className="w-full border-slate-200 rounded-lg p-4 bg-amber-50/30 border focus:ring-2 focus:ring-amber-500 outline-none placeholder:text-slate-400"
                placeholder="What resources, specs, or tools were missing?"
              />
            </div>
            <div>
              <label className="flex items-center gap-2 text-sm font-bold text-blue-700 mb-2"><TrendingUp className="w-4 h-4"/> Future Improvements</label>
              <textarea 
                rows={4} value={future} onChange={e => setFuture(e.target.value)}
                className="w-full border-slate-200 rounded-lg p-4 bg-blue-50/30 border focus:ring-2 focus:ring-blue-500 outline-none placeholder:text-slate-400"
                placeholder="What needs to be improved for the next cycle?"
              />
            </div>
          </div>

          <div className="flex justify-end pt-4">
            <button type="submit" className="bg-orange-600 hover:bg-orange-700 text-white px-8 py-3 rounded-lg font-bold shadow-md transition">
              Upload Report
            </button>
          </div>
        </form>
      )}

      {activeTab === 'view' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex gap-4 items-center">
              <span className="font-semibold text-slate-700">Project:</span>
              <select value={projectId} onChange={e => setProjectId(e.target.value)} className="border-slate-200 rounded-md p-2 bg-slate-50 border outline-none">
                <option value="1">Yottaflex AI Migration</option>
                <option value="2">Enterprise Dashboard V2</option>
              </select>
            </div>
            <div className="flex gap-4 items-center">
              <span className="font-semibold text-slate-700">Filter By:</span>
              <select value={filterType} onChange={e => setFilterType(e.target.value)} className="border-slate-200 rounded-md p-2 bg-slate-50 border outline-none">
                <option value="">All Reports</option>
                <option value="Daily">Daily</option>
                <option value="Weekly">Weekly</option>
                <option value="Sprint">Sprint</option>
                <option value="Monthly">Monthly</option>
                <option value="Yearly">Yearly</option>
              </select>
            </div>
          </div>

          {loading ? (
             <div className="p-8 text-center text-slate-500">Loading reports...</div>
          ) : reports.length === 0 ? (
             <div className="p-12 text-center text-slate-500 bg-white border border-slate-200 rounded-xl shadow-sm">
                No reports found matching these filters.
             </div>
          ) : (
            <div className="grid grid-cols-1 gap-6">
              {reports.map((r, i) => (
                <Card key={i} className="bg-white border-slate-200 shadow-sm hover:border-orange-300 transition-all overflow-hidden">
                  <div className="bg-slate-50 px-6 py-3 border-b border-slate-200 flex justify-between items-center">
                    <div className="flex items-center gap-3">
                      <span className="bg-orange-100 text-orange-700 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">{r.report_type}</span>
                      <span className="font-extrabold text-slate-800">{r.timeframe_label}</span>
                    </div>
                    <span className="text-sm font-medium text-slate-500">{r.report_date}</span>
                  </div>
                  <CardContent className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                    {r.achievements && (
                      <div>
                        <h4 className="text-sm font-bold text-emerald-600 mb-1 flex items-center gap-1"><Target className="w-3 h-3"/> Achievements</h4>
                        <p className="text-slate-600 text-sm whitespace-pre-wrap bg-slate-50 p-3 rounded-lg border border-slate-100">{r.achievements}</p>
                      </div>
                    )}
                    {r.risks_identified && (
                      <div>
                        <h4 className="text-sm font-bold text-red-600 mb-1 flex items-center gap-1"><AlertTriangle className="w-3 h-3"/> Risks</h4>
                        <p className="text-slate-600 text-sm whitespace-pre-wrap bg-slate-50 p-3 rounded-lg border border-slate-100">{r.risks_identified}</p>
                      </div>
                    )}
                    {r.missing_requirements && (
                      <div>
                        <h4 className="text-sm font-bold text-amber-600 mb-1 flex items-center gap-1"><FileSearch className="w-3 h-3"/> Missing Requirements</h4>
                        <p className="text-slate-600 text-sm whitespace-pre-wrap bg-slate-50 p-3 rounded-lg border border-slate-100">{r.missing_requirements}</p>
                      </div>
                    )}
                    {r.future_improvements && (
                      <div>
                        <h4 className="text-sm font-bold text-blue-600 mb-1 flex items-center gap-1"><TrendingUp className="w-3 h-3"/> Future Improvements</h4>
                        <p className="text-slate-600 text-sm whitespace-pre-wrap bg-slate-50 p-3 rounded-lg border border-slate-100">{r.future_improvements}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ProcessEngineering;
