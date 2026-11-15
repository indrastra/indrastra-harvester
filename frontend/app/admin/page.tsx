import AdminConsole from "@/components/admin-console";

export const metadata = {
  title: "Administration",
  description: "Manage repositories and harvesting jobs.",
};

export default function AdminPage() {
  return <AdminConsole />;
}
