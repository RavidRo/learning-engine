type StatCardProps = {
  label: string;
  value: number | string;
};

export const StatCard = ({ label, value }: StatCardProps) => (
  <div className="stat">
    <strong>{value}</strong>
    <span>{label}</span>
  </div>
);
