export const CustomersView = () => {
  return (
    <div>
      <h2 className="mb-2">Customer Management</h2>
      <div className="data-table">
        <p style={{ color: "#666", marginBottom: "1rem" }}>
          Use the AI Assistant to query customer information. Try asking:
        </p>
        <ul style={{ listStyle: "none", padding: 0 }}>
          <li style={{ padding: "0.5rem 0", borderBottom: "1px solid #e0e0e0" }}>
            💬 "List all customers"
          </li>
          <li style={{ padding: "0.5rem 0", borderBottom: "1px solid #e0e0e0" }}>
            💬 "Find customer with email john@example.com"
          </li>
          <li style={{ padding: "0.5rem 0", borderBottom: "1px solid #e0e0e0" }}>
            💬 "Show customers who spent over 50000"
          </li>
          <li style={{ padding: "0.5rem 0", borderBottom: "1px solid #e0e0e0" }}>
            💬 "List top 10 customers by spending"
          </li>
          <li style={{ padding: "0.5rem 0" }}>
            💬 "Show customers with more than 3 bookings"
          </li>
        </ul>
      </div>
    </div>
  );
};
