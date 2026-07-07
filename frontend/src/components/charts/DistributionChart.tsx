import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";

const COLORS = ["#cf8a00", "#0ea5e9", "#10b981", "#f2a900", "#ef4444", "#8b5cf6", "#7c4a05"];

interface DistributionChartProps {
  title: string;
  data: Array<Record<string, unknown>>;
  nameKey: string;
  valueKey: string;
}

export function DistributionChart({ title, data, nameKey, valueKey }: DistributionChartProps) {
  const hasData = data.some((d) => Number(d[valueKey]) > 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="h-64">
        {hasData ? (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={data} dataKey={valueKey} nameKey={nameKey} innerRadius={45} outerRadius={75} paddingAngle={2}>
                {data.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e2e8f0" }} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-slate-400">
            No data yet
          </div>
        )}
      </CardContent>
    </Card>
  );
}
