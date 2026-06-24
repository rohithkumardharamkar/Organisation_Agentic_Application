import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { api } from '../lib/api';

const ProjectIntelligence: React.FC = () => {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await api.dashboards.projects();
        setData(result);
      } catch (error) {
        console.error("Failed to fetch project dashboard data", error);
      }
    };
    fetchData();
  }, []);

  if (!data) return <div className="p-8 text-slate-900">Loading...</div>;

  return (
    <div className="p-8 space-y-8 bg-transparent min-h-screen text-slate-900">
      <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
        Project Intelligence
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-white border-slate-200 shadow-sm hover:border-emerald-400 transition-all">
          <CardHeader>
            <CardTitle className="text-slate-600">Project Health Score</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-6xl font-black text-emerald-500">{data.project_health_score}</div>
          </CardContent>
        </Card>
        
        <Card className="bg-white border-slate-200 shadow-sm hover:border-teal-400 transition-all">
          <CardHeader>
            <CardTitle className="text-slate-600">Resource Coverage</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-6xl font-black text-teal-500">{data.resource_coverage}</div>
          </CardContent>
        </Card>

        <Card className="bg-white border-slate-200 shadow-sm hover:border-blue-400 transition-all">
          <CardHeader>
            <CardTitle className="text-slate-600">Delivery Forecast</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-5xl font-black text-blue-500 mt-2">{data.delivery_forecast}</div>
          </CardContent>
        </Card>
      </div>

      <div className="mt-8">
        <h2 className="text-2xl font-bold mb-4 text-slate-800">Delay Risks Detected</h2>
        <div className="space-y-4">
          {data.delay_risks.map((risk: any, i: number) => (
            <div key={i} className="p-6 bg-red-50 border border-red-200 rounded-xl flex justify-between items-center hover:bg-red-100 transition shadow-sm">
              <div>
                <h3 className="text-xl font-bold text-red-600">{risk.project_name}</h3>
                <p className="text-red-500/80 mt-1">Delay Probability: {(risk.delay_probability * 100).toFixed(0)}%</p>
              </div>
              <div className="bg-white text-red-500 px-4 py-2 rounded-lg font-bold border border-red-200 shadow-sm">
                {risk.risk_level} Risk
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ProjectIntelligence;
