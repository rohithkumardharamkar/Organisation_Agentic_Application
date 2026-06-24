import React, { useEffect, useState } from 'react';
import { Card, CardContent } from '../components/ui/card';

const DataDirectory: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'employees' | 'projects'>('employees');
  const [employees, setEmployees] = useState<any[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulated fetch since DB might be empty initially
    const fetchData = async () => {
      setLoading(true);
      try {
        const empRes = await fetch('http://localhost:8000/api/v1/workforce/employees');
        const empData = await empRes.json();
        
        const projRes = await fetch('http://localhost:8000/api/v1/workforce/projects');
        const projData = await projRes.json();

        // Use mock data if API returns empty (for demonstration)
        setEmployees(empData.length > 0 ? empData : [
          { id: '1', name: 'John Doe', department: 'Engineering', role: 'Senior Developer', utilization: 85, status: 'Active' },
          { id: '2', name: 'Jane Smith', department: 'Sales', role: 'Account Executive', utilization: 90, status: 'Active' },
          { id: '3', name: 'Alice Johnson', department: 'Marketing', role: 'Content Strategist', utilization: 40, status: 'Bench' }
        ]);

        setProjects(projData.length > 0 ? projData : [
          { id: '1', name: 'Project Alpha', status: 'In Progress', budget: '$150,000', deadline: '2026-09-30' },
          { id: '2', name: 'Project Beta', status: 'At Risk', budget: '$200,000', deadline: '2026-10-15' }
        ]);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="p-8 space-y-8 bg-transparent min-h-screen text-slate-900">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            Data Directory
          </h1>
          <p className="text-slate-500 text-lg mt-1">Centralized Workforce & Project Repository</p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={() => setActiveTab('employees')}
            className={`px-6 py-2.5 rounded-lg font-semibold transition-all ${activeTab === 'employees' ? 'bg-blue-600 text-white shadow-md' : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'}`}
          >
            Employees
          </button>
          <button 
            onClick={() => setActiveTab('projects')}
            className={`px-6 py-2.5 rounded-lg font-semibold transition-all ${activeTab === 'projects' ? 'bg-blue-600 text-white shadow-md' : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'}`}
          >
            Projects
          </button>
        </div>
      </div>

      <Card className="bg-white border-slate-200 shadow-sm overflow-hidden">
        <CardContent className="p-0">
          {loading ? (
            <div className="p-12 text-center text-slate-500 font-medium">Loading data directory...</div>
          ) : activeTab === 'employees' ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 text-sm uppercase tracking-wider">
                    <th className="p-4 font-semibold">Employee Name</th>
                    <th className="p-4 font-semibold">Department</th>
                    <th className="p-4 font-semibold">Role</th>
                    <th className="p-4 font-semibold">Utilization</th>
                    <th className="p-4 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {employees.map((emp, i) => (
                    <tr key={i} className="hover:bg-slate-50/50 transition-colors">
                      <td className="p-4 font-medium text-slate-900">{emp.name}</td>
                      <td className="p-4 text-slate-600">{emp.department}</td>
                      <td className="p-4 text-slate-600">{emp.role}</td>
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <div className="w-full bg-slate-200 rounded-full h-2 max-w-[100px]">
                            <div className={`h-2 rounded-full ${emp.utilization > 80 ? 'bg-emerald-500' : emp.utilization < 50 ? 'bg-amber-500' : 'bg-blue-500'}`} style={{ width: `${emp.utilization}%` }}></div>
                          </div>
                          <span className="text-sm font-semibold text-slate-700">{emp.utilization}%</span>
                        </div>
                      </td>
                      <td className="p-4">
                        <span className={`px-3 py-1 rounded-full text-xs font-bold ${emp.status === 'Active' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                          {emp.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 text-sm uppercase tracking-wider">
                    <th className="p-4 font-semibold">Project Name</th>
                    <th className="p-4 font-semibold">Budget</th>
                    <th className="p-4 font-semibold">Deadline</th>
                    <th className="p-4 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {projects.map((proj, i) => (
                    <tr key={i} className="hover:bg-slate-50/50 transition-colors">
                      <td className="p-4 font-medium text-slate-900">{proj.name}</td>
                      <td className="p-4 text-slate-600 font-mono">{proj.budget}</td>
                      <td className="p-4 text-slate-600">{proj.deadline}</td>
                      <td className="p-4">
                        <span className={`px-3 py-1 rounded-full text-xs font-bold ${proj.status === 'In Progress' ? 'bg-blue-100 text-blue-700' : 'bg-red-100 text-red-700'}`}>
                          {proj.status}
                        </span>
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
  );
};

export default DataDirectory;
