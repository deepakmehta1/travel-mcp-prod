export const BookingsView = () => {
  return (
    <div>
      <h2 className="mb-2">Bookings Management</h2>
      <div className="data-table">
        <p style={{ color: "#666", marginBottom: "1rem" }}>
          Use the AI Assistant to query and manage bookings. Try asking:
        </p>
        <ul style={{ listStyle: "none", padding: 0 }}>
          <li style={{ padding: "0.5rem 0", borderBottom: "1px solid #e0e0e0" }}>
            💬 "Show me all confirmed bookings"
          </li>
          <li style={{ padding: "0.5rem 0", borderBottom: "1px solid #e0e0e0" }}>
            💬 "List pending bookings"
          </li>
          <li style={{ padding: "0.5rem 0", borderBottom: "1px solid #e0e0e0" }}>
            💬 "Show bookings for Goa destination"
          </li>
          <li style={{ padding: "0.5rem 0", borderBottom: "1px solid #e0e0e0" }}>
            💬 "Get bookings starting next month"
          </li>
          <li style={{ padding: "0.5rem 0" }}>
            💬 "Update booking 123 to confirmed"
          </li>
        </ul>
      </div>
    </div>
  );
};
