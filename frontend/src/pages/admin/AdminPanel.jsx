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
  adminUsers,
  resetDemo,
  seedDemo,
  testEmail,
  updateUserRole
} from "../../api/admin";

const roles = ["applicant", "surveyor", "registrar", "supervisor", "admin"];

export default function AdminPanel() {
  const [data, setData] = useState({ applicants: [], applications: [], staff: [], events: [], notificationEvents: [], notificationMessages: [], users: [] });
  const [userSearch, setUserSearch] = useState("");
  const [roleEdits, setRoleEdits] = useState({});
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [testRecipient, setTestRecipient] = useState("");

  async function load() {
    setError("");
    try {
      const [applicants, applications, staff, events, notificationEvents, notificationMessages, users] = await Promise.all([
        adminApplicants(),
        adminApplications(),
        adminStaff(),
        adminSystemEvents(),
        adminNotificationEvents(),
        adminNotificationMessages(),
        adminUsers({ search: userSearch })
      ]);
      setData({
        applicants: applicants.items || [],
        applications: applications.items || [],
        staff: staff.items || [],
        events: events.items || [],
        notificationEvents: notificationEvents.items || [],
        notificationMessages: notificationMessages.items || [],
        users: users.items || []
      });
      setRoleEdits((current) => {
        const next = { ...current };
        for (const user of users.items || []) {
          next[user.user_id] = next[user.user_id] || { role: user.role, actor_id: user.actor_id || "" };
        }
        return next;
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

  function editUser(userId, field, value) {
    setRoleEdits((current) => ({ ...current, [userId]: { ...(current[userId] || {}), [field]: value } }));
  }

  function saveRole(user) {
    const edit = roleEdits[user.user_id] || { role: user.role, actor_id: user.actor_id || "" };
    return run(
      () => updateUserRole(user.user_id, { role: edit.role, actor_id: edit.actor_id || null }),
      `Role updated for ${user.email}.`
    );
  }

  return (
    <Panel title="Admin Panel" actions={<button onClick={load}>Refresh</button>}>
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
        <div className="metric"><span>Users</span><strong>{data.users.length}</strong></div>
        <div className="metric"><span>System events</span><strong>{data.events.length}</strong></div>
        <div className="metric"><span>Notifications</span><strong>{data.notificationEvents.length}</strong></div>
        <div className="metric"><span>Email messages</span><strong>{data.notificationMessages.length}</strong></div>
      </div>
      <section>
        <h3>User emails and roles</h3>
        <div className="inline-form">
          <input
            placeholder="search email, name, role, actor id"
            value={userSearch}
            onChange={(event) => setUserSearch(event.target.value)}
          />
          <button onClick={load}>Search</button>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Email</th>
              <th>Name</th>
              <th>Verified</th>
              <th>Role</th>
              <th>Actor ID</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {data.users.map((user) => {
              const edit = roleEdits[user.user_id] || { role: user.role, actor_id: user.actor_id || "" };
              return (
                <tr key={user.user_id}>
                  <td>{user.email}</td>
                  <td>{user.full_name}</td>
                  <td>{user.email_verified ? "yes" : "no"}</td>
                  <td>
                    <select value={edit.role} onChange={(event) => editUser(user.user_id, "role", event.target.value)}>
                      {roles.map((role) => <option key={role} value={role}>{role}</option>)}
                    </select>
                  </td>
                  <td>
                    <input value={edit.actor_id} onChange={(event) => editUser(user.user_id, "actor_id", event.target.value)} placeholder="auto for staff roles" />
                  </td>
                  <td><button onClick={() => saveRole(user)}>Update</button></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
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
