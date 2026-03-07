import { useState } from "react";
import { AdminAgentClient } from "./api/client";
import { Header } from "./components/Header";
import { Sidebar } from "./components/Sidebar";
import { Dashboard } from "./components/Dashboard";
import { ChatInterface } from "./components/ChatInterface";
import { BookingsView } from "./components/BookingsView";
import { CustomersView } from "./components/CustomersView";
import { ToursView } from "./components/ToursView";
import "./styles.css";

const client = new AdminAgentClient();

function App() {
  const [activeView, setActiveView] = useState("dashboard");

  const handleReset = async () => {
    await client.reset();
    window.location.reload();
  };

  const renderView = () => {
    switch (activeView) {
      case "dashboard":
        return <Dashboard />;
      case "chat":
        return <ChatInterface client={client} />;
      case "bookings":
        return <BookingsView />;
      case "customers":
        return <CustomersView />;
      case "tours":
        return <ToursView />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div>
      <Header onReset={handleReset} />
      <div className="admin-container">
        <Sidebar activeView={activeView} onViewChange={setActiveView} />
        <div className="main-content">{renderView()}</div>
      </div>
    </div>
  );
}

export default App;
