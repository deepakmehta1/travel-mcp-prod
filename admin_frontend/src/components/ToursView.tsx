export const ToursView = () => {
  return (
    <div>
      <h2 className="mb-2">Tours Management</h2>
      <div className="data-table">
        <p style={{ color: "#666", marginBottom: "1rem" }}>
          Use the AI Assistant to query tour performance. Try asking:
        </p>
        <ul style={{ listStyle: "none", padding: 0 }}>
          <li style={{ padding: "0.5rem 0", borderBottom: "1px solid #e0e0e0" }}>
            💬 "List all tours"
          </li>
          <li style={{ padding: "0.5rem 0", borderBottom: "1px solid #e0e0e0" }}>
            💬 "Show tours to Goa"
          </li>
          <li style={{ padding: "0.5rem 0", borderBottom: "1px solid #e0e0e0" }}>
            💬 "Which tours have the most bookings?"
          </li>
          <li style={{ padding: "0.5rem 0", borderBottom: "1px solid #e0e0e0" }}>
            💬 "Show tours with highest revenue"
          </li>
          <li style={{ padding: "0.5rem 0" }}>
            💬 "List tours with no bookings"
          </li>
        </ul>
      </div>
    </div>
  );
};
