import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { api } from '../lib/api';

const TalentIntelligence: React.FC = () => {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await api.dashboards.talent();
        setData(result);
      } catch (error) {
        console.error("Failed to fetch talent dashboard data", error);
      }
    };
    fetchData();
  }, []);

  if (!data) return <div className="p-8 text-slate-900">Loading...</div>;

  return (
    <div className="p-8 space-y-8 bg-transparent min-h-screen text-slate-900">
      <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
        Talent Intelligence
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-white border-slate-200 shadow-sm hover:border-purple-400 transition-all">
          <CardHeader>
            <CardTitle className="text-slate-600">Skills Inventory</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(data.skills_inventory).map(([skill, count]: [string, any], i) => (
                <div key={i} className="flex justify-between items-center">
                  <span className="font-semibold text-slate-700">{skill}</span>
                  <span className="font-bold text-purple-600 bg-purple-100 px-3 py-1 rounded-md">{count} Employees</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-white border-slate-200 shadow-sm hover:border-pink-400 transition-all flex flex-col justify-center text-center p-8">
          <CardHeader>
            <CardTitle className="text-slate-600">Future Demand Forecast</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-black text-pink-600 mt-4 leading-snug">{data.future_demand_forecast}</div>
          </CardContent>
        </Card>
      </div>

      <div className="mt-8">
        <h2 className="text-2xl font-bold mb-4 text-slate-800">Skill Gaps & Hiring AI Recommendations</h2>
        <div className="space-y-4">
          {data.skill_gaps.map((gap: any, i: number) => (
            <div key={i} className="p-6 bg-white border border-slate-200 shadow-sm rounded-xl hover:border-amber-400 transition-all">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-xl font-bold text-amber-600">{gap.skill} Gap Detected</h3>
                  <p className="text-slate-600 mt-2 max-w-2xl">{gap.recommendation}</p>
                </div>
                <div className="bg-amber-50 text-amber-600 px-4 py-2 rounded-lg font-bold border border-amber-200">
                  Risk: {(gap.shortage_probability * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TalentIntelligence;
