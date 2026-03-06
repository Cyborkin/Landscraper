import { useParams } from "react-router-dom";
export default function LeadDetail() {
  const { leadId } = useParams<{ leadId: string }>();
  return <div className="text-text-secondary">Lead Detail: {leadId}</div>;
}
