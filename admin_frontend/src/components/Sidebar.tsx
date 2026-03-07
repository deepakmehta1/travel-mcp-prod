interface SidebarProps {
  activeView: string;
  onViewChange: (view: string) => void;
}

export const Sidebar = ({ activeView, onViewChange }: SidebarProps) => {
  const menuItems = [
    { id: "dashboard", label: "📊 Dashboard", icon: "📊" },
    { id: "chat", label: "💬 AI Assistant", icon: "💬" },
    { id: "bookings", label: "📋 Bookings", icon: "📋" },
    { id: "customers", label: "👥 Customers", icon: "👥" },
    { id: "tours", label: "🌍 Tours", icon: "🌍" },
  ];

  return (
    <div className="sidebar">
      <ul className="sidebar-menu">
        {menuItems.map((item) => (
          <li key={item.id}>
            <button
              className={activeView === item.id ? "active" : ""}
              onClick={() => onViewChange(item.id)}
            >
              {item.label}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
};
