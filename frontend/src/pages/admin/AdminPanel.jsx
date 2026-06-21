import { useEffect, useState } from "react";
import Panel from "../../components/Panel";
import Message from "../../components/Message";
import {
  adminApplicants,
  adminApplications,
  adminNotificationEvents,
  adminNotificationMessages,
  adminStaff,
  adminSystemEvents,
  resetDemo,
  seedDemo,
  testEmail
} from "../../api/admin";

export default function AdminPanel() {
  const [data, setData] = useState({ applicants: [], applications: [], staff: [], events: [], notificationEvents: [], notificationMessages: [] });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [testRecipient, setTestRecipient] = useState("");

  async function load() {
    setError("");
    try {
      const [applicants, applications, staff, events, notificationEvents, notificationMessages] = await Promise.all([
        adminApplicants(),
        adminApplications(),
        adminStaff(),
        adminSystemEvents(),
        adminNotificationEvents(),
        adminNotificationMessages()
      ]);
      setData({
        applicants: applicants.items || [],
        applications: applications.items || [],
        staff: staff.items || [],
        events: events.items || [],
        notificationEvents: notificationEvents.items || [],
        notificationMessages: notificationMessages.items || []
      });
    } catch (err) {
      setError(err.message);
    }
  }

  async function run(action, success) {
    setError("");
    setMessage("");
    try {
      await action();
      setMessage(success);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <Panel title="Supervisor / Admin Panel" actions={<button onClick={load}>Refresh</button>}>
      <Message error={error}>{message}</Message>
      <div className="panel-actions">
        <button onClick={() => run(seedDemo, "Demo data seeded.")}>Seed demo data</button>
        <button className="danger" onClick={() => run(resetDemo, "Demo data reset.")}>Reset demo data</button>
      </div>
      <div className="inline-form">
        <input
          type="email"
          placeholder="test recipient email"
          value={testRecipient}
          onChange={(event) => setTestRecipient(event.target.value)}
        />
        <button onClick={() => run(() => testEmail(testRecipient || null), "Test email notification queued.")}>Send test email</button>
      </div>
      <div className="grid">
        <div className="metric"><span>Applicants</span><strong>{data.applicants.length}</strong></div>
        <div className="metric"><span>Applications</span><strong>{data.applications.length}</strong></div>
        <div className="metric"><span>Staff</span><strong>{data.staff.length}</strong></div>
        <div className="metric"><span>System events</span><strong>{data.events.length}</strong></div>
        <div className="metric"><span>Notifications</span><strong>{data.notificationEvents.length}</strong></div>
        <div className="metric"><span>Email messages</span><strong>{data.notificationMessages.length}</strong></div>
      </div>
      <div className="detail-grid">
        <section>
          <h3>Staff</h3>
          {(data.staff || []).map((item) => (
            <p key={item.staff_code}><strong>{item.staff_code}</strong> {item.name} - {item.role}</p>
          ))}
        </section>
        <section>
          <h3>Recent audit / rate-limit events</h3>
          {(data.events || []).slice(0, 12).map((event) => (
            <p key={event._id || `${event.event_type}-${event.timestamp}`}>
              <strong>{event.event_type}</strong> {event.actor?.email || event.actor?.role || ""} {event.timestamp}
            </p>
          ))}
        </section>
        <section>
          <h3>Email delivery</h3>
          {(data.notificationMessages || []).slice(0, 12).map((item) => (
            <p key={item.message_id}>
              <strong>{item.status}</strong> {item.to_email} - {item.subject}
            </p>
          ))}
        </section>
      </div>
    </Panel>
  );
}
