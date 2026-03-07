export const Dashboard = () => {
  return (
    <div>
      <h2 className="mb-2">Dashboard Overview</h2>
      <div className="dashboard-grid">
        <div className="stat-card">
          <h3>Total Bookings</h3>
          <div className="value">--</div>
          <p style={{ color: "#666", fontSize: "0.9rem", marginTop: "0.5rem" }}>
            Use AI Assistant to get live data
          </p>
        </div>
        <div className="stat-card">
          <h3>Total Revenue</h3>
          <div className="value">--</div>
          <p style={{ color: "#666", fontSize: "0.9rem", marginTop: "0.5rem" }}>
            Use AI Assistant to get live data
          </p>
        </div>
        <div className="stat-card">
          <h3>Active Customers</h3>
          <div className="value">--</div>
          <p style={{ color: "#666", fontSize: "0.9rem", marginTop: "0.5rem" }}>
            Use AI Assistant to get live data
          </p>
        </div>
        <div className="stat-card">
          <h3>Pending Bookings</h3>
          <div className="value">--</div>
          <p style={{ color: "#666", fontSize: "0.9rem", marginTop: "0.5rem" }}>
            Use AI Assistant to get live data
          </p>
        </div>
      </div>
      
      <div className="data-table">
        <h3 className="mb-1">Quick Actions</h3>
        <p style={{ color: "#666", marginBottom: "1.5rem" }}>
          Use the AI Assistant to query and manage your travel booking data. Try asking:
        </p>
        <ul style={{ listStyle: "none", padding: 0 }}>
          <li style={{ padding: "0.75rem", background: "#f9f9f9", marginBottom: "0.5rem", borderRadius: "8px" }}>
            💬 "Show me all bookings from last month"
          </li>
          <li style={{ padding: "0.75rem", background: "#f9f9f9", marginBottom: "0.5rem", borderRadius: "8px" }}>
            💬 "What's our total revenue?"
          </li>
          <li style={{ padding: "0.75rem", background: "#f9f9f9", marginBottom: "0.5rem", borderRadius: "8px" }}>
            💬 "List top customers by spending"
          </li>
          <li style={{ padding: "0.75rem", background: "#f9f9f9", marginBottom: "0.5rem", borderRadius: "8px" }}>
            💬 "Show me tours with most bookings"
          </li>
          <li style={{ padding: "0.75rem", background: "#f9f9f9", marginBottom: "0.5rem", borderRadius: "8px" }}>
            💬 "Get revenue report for this year"
          </li>
        </ul>
      </div>
    </div>
  );
};
