import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { api } from '../lib/api';

const WorkforceIntelligence: React.FC = () => {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await api.dashboards.workforce();
        setData(result);
      } catch (error) {
        console.error("Failed to fetch workforce dashboard data", error);
      }
    };
    fetchData();
  }, []);

  if (!data) return <div className="p-8 text-slate-900">Loading...</div>;

  return (
    <div className="p-8 space-y-8 bg-transparent min-h-screen text-slate-900">
      <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
        Workforce Intelligence
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-white border-slate-200 shadow-sm hover:border-indigo-400 transition-all">
          <CardHeader>
            <CardTitle className="text-slate-600">Available Resources</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-6xl font-black text-indigo-500">{data.available_resources}</div>
          </CardContent>
        </Card>
        
        <Card className="bg-white border-slate-200 shadow-sm hover:border-amber-400 transition-all">
          <CardHeader>
            <CardTitle className="text-slate-600">Bench Resources</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-6xl font-black text-amber-500">{data.bench_resources}</div>
          </CardContent>
        </Card>

        <Card className="bg-white border-slate-200 shadow-sm hover:border-red-400 transition-all">
          <CardHeader>
            <CardTitle className="text-slate-600">Overallocated</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-6xl font-black text-red-500">{data.overallocated_employees}</div>
          </CardContent>
        </Card>
      </div>

      <div className="mt-8">
        <h2 className="text-2xl font-bold mb-4 text-slate-800">Department Utilization</h2>
        <div className="space-y-4">
          {Object.entries(data.utilization_heatmap).map(([dept, util]: [string, any], i) => (
            <div key={i} className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
              <div className="flex justify-between items-center mb-2">
                <span className="font-semibold text-lg text-slate-700">{dept}</span>
                <span className="font-bold text-blue-600">{util}%</span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-4">
                <div 
                  className={`h-4 rounded-full ${util > 85 ? 'bg-red-500' : util < 75 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                  style={{ width: `${util}%` }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default WorkforceIntelligence;
