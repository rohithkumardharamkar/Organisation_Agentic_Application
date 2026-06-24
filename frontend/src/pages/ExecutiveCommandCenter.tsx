import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { api } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { 
  FileText, Trash2, Upload, CheckCircle2, AlertTriangle, 
  Cpu, Users, Award, Shield, FileSpreadsheet, TrendingUp
} from 'lucide-react';

const ExecutiveCommandCenter: React.FC = () => {
  const { userRole } = useAuth();
  const [data, setData] = useState<any>(null);
  const [docs, setDocs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  
  // File upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [category, setCategory] = useState('Policies');
  const [allowedRoles, setAllowedRoles] = useState<string[]>(['all']);

  const loadData = async () => {
    try {
      setLoading(true);
      const [dashResult, docsResult] = await Promise.all([
        api.dashboards.executive(),
        api.knowledge.list()
      ]);
      setData(dashResult);
      setDocs(docsResult);
    } catch (error) {
      console.error("Failed to fetch Executive Command data", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRoleCheckbox = (role: string) => {
    if (role === 'all') {
      setAllowedRoles(['all']);
    } else {
      let updated = allowedRoles.filter(r => r !== 'all');
      if (updated.includes(role)) {
        updated = updated.filter(r => r !== role);
      } else {
        updated.push(role);
      }
      if (updated.length === 0) updated = ['all'];
      setAllowedRoles(updated);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setUploadError("Please select a valid document to upload.");
      return;
    }
    
    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);
    
    try {
      const rolesParam = allowedRoles.join(',');
      const res = await api.knowledge.upload(selectedFile, category, rolesParam);
      setUploadSuccess(res.message || "Document uploaded and indexed in knowledge base successfully!");
      setSelectedFile(null);
      await loadData();
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || "Failed to index document in the knowledge base.");
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDoc = async (id: number) => {
    if (!confirm("Are you sure you want to delete this document from the Qdrant index and SQLite database?")) return;
    try {
      await api.knowledge.delete(id);
      await loadData();
    } catch (err) {
      console.error("Failed to delete document", err);
    }
  };

  if (userRole !== 'HR') {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[80vh] text-center">
        <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center text-red-600 mb-4 shadow-md">
          <Shield className="w-8 h-8" />
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight mb-2">Access Denied</h1>
        <p className="text-slate-500 max-w-md">
          Your current security clearance level (**{userRole}**) is not authorized to access the Executive Command Center.
        </p>
      </div>
    );
  }

  if (loading && !data) {
    return (
      <div className="p-8 space-y-4 animate-pulse">
        <div className="h-10 bg-slate-200 rounded-lg w-1/4"></div>
        <div className="h-4 bg-slate-200 rounded-lg w-1/3"></div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-8">
          {[...Array(10)].map((_, i) => (
            <div key={i} className="h-24 bg-slate-200 rounded-2xl"></div>
          ))}
        </div>
      </div>
    );
  }

  const metricsList = [
    { label: 'Total Employees', value: data?.metrics?.total_employees ?? 0, icon: Users, color: 'text-blue-600', bg: 'bg-blue-50/60' },
    { label: 'Active Employees', value: data?.metrics?.active_employees ?? 0, icon: CheckCircle2, color: 'text-emerald-600', bg: 'bg-emerald-50/60' },
    { label: 'Utilization %', value: `${data?.metrics?.utilization_percentage ?? 0}%`, icon: Award, color: 'text-indigo-600', bg: 'bg-indigo-50/60' },
    { label: 'Bench %', value: `${data?.metrics?.bench_percentage ?? 0}%`, icon: AlertTriangle, color: 'text-amber-600', bg: 'bg-amber-50/60' },
    { label: 'Project Health', value: `${data?.metrics?.project_health ?? 0}%`, icon: Cpu, color: 'text-teal-600', bg: 'bg-teal-50/60' },
    { label: 'Resource Demand', value: data?.metrics?.resource_demand ?? 0, icon: FileSpreadsheet, color: 'text-sky-600', bg: 'bg-sky-50/60' },
    { label: 'Hiring Demand', value: data?.metrics?.hiring_demand ?? 0, icon: Users, color: 'text-pink-600', bg: 'bg-pink-50/60' },
    { label: 'Skill Gaps', value: data?.metrics?.skill_gaps ?? 0, icon: AlertTriangle, color: 'text-red-600', bg: 'bg-red-50/60' },
    { label: 'Risky Projects', value: data?.metrics?.risky_projects ?? 0, icon: AlertTriangle, color: 'text-orange-600', bg: 'bg-orange-50/60' },
    { label: 'Delivery Health', value: `${data?.metrics?.delivery_health ?? 0}%`, icon: Shield, color: 'text-violet-600', bg: 'bg-violet-50/60' },
  ];

  return (
    <div className="p-8 space-y-8 bg-transparent min-h-screen text-slate-900">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-6">
        <div>
          <h1 className="text-4xl font-black tracking-tight bg-gradient-to-r from-blue-700 via-indigo-600 to-emerald-600 bg-clip-text text-transparent flex items-center gap-3">
            <Cpu className="w-9 h-9 text-blue-600 animate-pulse" />
            Executive Command Center
          </h1>
          <p className="text-slate-500 mt-1.5 text-lg font-medium">AI-Driven Organizational Intelligence & Workforce Telemetry</p>
        </div>
        <button 
          onClick={loadData}
          className="px-5 py-2.5 rounded-xl bg-slate-950 hover:bg-slate-800 text-white font-semibold shadow-md transition duration-200 active:scale-95"
        >
          Refresh Telemetry
        </button>
      </div>

      {/* 10 Executive Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-5">
        {metricsList.map((m, idx) => {
          const Icon = m.icon;
          return (
            <Card key={idx} className="bg-white border border-slate-200 shadow-sm relative overflow-hidden rounded-2xl hover:shadow-md hover:border-slate-300 transition-all duration-300">
              <div className="p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400 font-bold text-xs tracking-wider uppercase">{m.label}</span>
                  <div className={`p-1.5 rounded-lg ${m.bg}`}>
                    <Icon className={`w-4 h-4 ${m.color}`} />
                  </div>
                </div>
                <div className="flex items-baseline">
                  <span className="text-3xl font-black tracking-tight text-slate-900">{m.value}</span>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Split layout for AI Insights Panel & Document Management */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left/Middle: AI Insights Panel */}
        <div className="lg:col-span-7 space-y-6">
          <h2 className="text-2xl font-black text-slate-800 tracking-tight flex items-center gap-2.5">
            <TrendingUp className="w-6 h-6 text-indigo-600" />
            AI Insights & Recommendations
          </h2>

          <div className="grid grid-cols-1 gap-5">
            {/* Top Risks */}
            <Card className="bg-white border border-slate-200 rounded-2xl shadow-sm hover:border-slate-300 transition duration-300">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-bold text-red-600 tracking-wider uppercase flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-500" />
                  Top Risks
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="list-disc pl-4 space-y-1.5 text-slate-600 text-sm font-medium">
                  {data?.ai_insights?.top_risks?.map((risk: string, i: number) => (
                    <li key={i}>{risk}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            {/* Recommended Actions */}
            <Card className="bg-white border border-slate-200 rounded-2xl shadow-sm hover:border-slate-300 transition duration-300">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-bold text-indigo-600 tracking-wider uppercase flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-indigo-500" />
                  Recommended C-Suite Actions
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="list-disc pl-4 space-y-1.5 text-slate-600 text-sm font-medium">
                  {data?.ai_insights?.recommended_actions?.map((act: string, i: number) => (
                    <li key={i}>{act}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            {/* Hiring Needs */}
            <Card className="bg-white border border-slate-200 rounded-2xl shadow-sm hover:border-slate-300 transition duration-300">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-bold text-pink-600 tracking-wider uppercase flex items-center gap-2">
                  <Users className="w-4 h-4 text-pink-500" />
                  Hiring Needs
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="list-disc pl-4 space-y-1.5 text-slate-600 text-sm font-medium">
                  {data?.ai_insights?.hiring_needs?.map((need: string, i: number) => (
                    <li key={i}>{need}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            {/* Resource Issues */}
            <Card className="bg-white border border-slate-200 rounded-2xl shadow-sm hover:border-slate-300 transition duration-300">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-bold text-amber-600 tracking-wider uppercase flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-500" />
                  Resource Issues
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="list-disc pl-4 space-y-1.5 text-slate-600 text-sm font-medium">
                  {data?.ai_insights?.resource_issues?.map((issue: string, i: number) => (
                    <li key={i}>{issue}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            {/* Skill Shortages */}
            <Card className="bg-white border border-slate-200 rounded-2xl shadow-sm hover:border-slate-300 transition duration-300">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-bold text-violet-600 tracking-wider uppercase flex items-center gap-2">
                  <Award className="w-4 h-4 text-violet-500" />
                  Skill Shortages & single-points
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="list-disc pl-4 space-y-1.5 text-slate-600 text-sm font-medium">
                  {data?.ai_insights?.skill_shortages?.map((short: string, i: number) => (
                    <li key={i}>{short}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Right: Document Uploader (RAG) */}
        <div className="lg:col-span-5">
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6 hover:border-slate-300 transition duration-300">
            <h2 className="text-2xl font-black text-slate-800 tracking-tight flex items-center gap-2">
              <Upload className="w-6 h-6 text-blue-600" />
              Upload RAG Knowledge base
            </h2>

            <form onSubmit={handleUploadSubmit} className="space-y-5">
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700">Select Document File</label>
                <div className="border-2 border-dashed border-slate-200 rounded-xl p-6 flex flex-col items-center justify-center hover:border-blue-400 transition cursor-pointer relative bg-slate-50">
                  <input 
                    type="file" 
                    accept=".pdf,.docx,.pptx,.txt"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  />
                  <FileSpreadsheet className="w-10 h-10 text-slate-400 mb-2" />
                  <span className="text-slate-600 font-bold text-sm text-center px-4 break-all">
                    {selectedFile ? selectedFile.name : "Click to select a file"}
                  </span>
                  <span className="text-slate-400 text-xs mt-1">Supports PDF, DOCX, PPTX, TXT</span>
                </div>
              </div>

              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-bold text-slate-700">Document Category</label>
                  <select 
                    value={category} 
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 px-3 py-2.5 bg-white text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                  >
                    <option value="Policies">Policies</option>
                    <option value="SOPs">SOPs</option>
                    <option value="Guidelines">Guidelines</option>
                    <option value="Handbooks">Handbooks</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-bold text-slate-700 flex items-center gap-1.5">
                    Allowed Access Roles
                  </label>
                  <div className="flex flex-col gap-1 text-sm bg-slate-50 p-3 rounded-xl border border-slate-100">
                    {['all', 'Employee', 'Reporting Manager', 'Process Engineer'].map((role) => (
                      <label key={role} className="flex items-center gap-2 cursor-pointer py-1">
                        <input 
                          type="checkbox" 
                          checked={allowedRoles.includes(role)} 
                          onChange={() => handleRoleCheckbox(role)}
                          className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 w-4 h-4"
                        />
                        <span className="font-semibold text-slate-700">{role === 'all' ? 'All Roles (Public)' : role}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              {uploadSuccess && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-xl text-sm font-semibold">
                  {uploadSuccess}
                </div>
              )}

              {uploadError && (
                <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm font-semibold">
                  {uploadError}
                </div>
              )}

              <button 
                type="submit" 
                disabled={uploading || !selectedFile}
                className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-slate-300 text-white font-bold py-3 rounded-xl shadow-md transition duration-200 flex items-center justify-center gap-2"
              >
                {uploading ? "Indexing document contents..." : "Upload & Run Vector Index"}
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Document Directory */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm hover:border-slate-300 transition duration-300">
        <h2 className="text-2xl font-black text-slate-800 tracking-tight flex items-center gap-2 mb-6">
          <FileText className="w-6 h-6 text-indigo-600" />
          Knowledge Base Directory
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-400 font-bold uppercase tracking-wider text-xs">
                <th className="pb-3 pl-2">Filename</th>
                <th className="pb-3">Category</th>
                <th className="pb-3">Uploaded By</th>
                <th className="pb-3">Allowed Roles</th>
                <th className="pb-3">Uploaded At</th>
                <th className="pb-3 text-right pr-2">Action</th>
              </tr>
            </thead>
            <tbody>
              {docs.length > 0 ? (
                docs.map((doc) => (
                  <tr key={doc.id} className="border-b border-slate-100 hover:bg-slate-50/80 transition">
                    <td className="py-4 pl-2 font-semibold text-slate-900 max-w-[200px] truncate">{doc.filename}</td>
                    <td className="py-4 text-slate-500">
                      <span className="bg-slate-100 px-2.5 py-1 rounded-lg text-xs font-bold text-slate-600">
                        {doc.category}
                      </span>
                    </td>
                    <td className="py-4 text-slate-500 font-medium">{doc.uploaded_by}</td>
                    <td className="py-4 text-slate-500">
                      <div className="flex flex-wrap gap-1">
                        {doc.allowed_roles.map((r: string) => (
                          <span key={r} className="bg-blue-50 px-2 py-0.5 rounded text-xs font-semibold text-blue-700 border border-blue-100">
                            {r}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-4 text-slate-500 font-medium">{doc.uploaded_at?.split(' ')?.[0] || 'N/A'}</td>
                    <td className="py-4 text-right pr-2">
                      <button 
                        onClick={() => handleDeleteDoc(doc.id)}
                        className="p-2 rounded-lg text-red-500 hover:bg-red-50 transition"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400 font-semibold">
                    No documents indexed in the knowledge base. Use the form above to upload some.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ExecutiveCommandCenter;
