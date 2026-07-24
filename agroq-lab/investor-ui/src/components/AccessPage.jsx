import {
  BadgeDollarSign,
  Handshake,
  KeyRound,
  LogIn,
  Rocket,
  Users,
} from "lucide-react";

const backendBase =
  import.meta.env.VITE_AGROQ_BACKEND_URL || "http://127.0.0.1:5000";

const cards = [
  ["Sign in", "Open the authenticated research and operations workspace.", LogIn, "/login"],
  ["Redeem invitation", "Create a role-controlled profile with a temporary code.", KeyRound, "/access/redeem"],
  ["Join the beta", "Request prototype access and structured product testing.", Rocket, "/access?type=beta_tester"],
  ["Investor access", "Request a private funding and diligence conversation.", BadgeDollarSign, "/access?type=investor"],
  ["Contribute", "Join the engineering, research, or open-source effort.", Users, "/access?type=contributor"],
  ["Partner with AgroQ", "Explore university, farm, and technology partnerships.", Handshake, "/access?type=partner"],
];

export default function AccessPage() {
  const open = (path) => window.location.assign(`${backendBase}${path}`);

  return (
    <div className="page-stack">
      <section className="panel access-community-hero">
        <div>
          <span className="eyebrow">ACCESS & COMMUNITY</span>
          <h2>One platform. Multiple ways to participate.</h2>
          <p>
            Relationship type and application permissions remain separate so
            investors, beta users, contributors, partners, researchers, and
            operators receive the right experience.
          </p>
        </div>
      </section>

      <section className="access-entry-grid">
        {cards.map(([title, copy, Icon, path]) => (
          <article className="panel access-entry-card" key={title}>
            <div className="access-entry-icon"><Icon size={23} /></div>
            <h3>{title}</h3>
            <p>{copy}</p>
            <button className="button button-secondary full-width" onClick={() => open(path)}>
              Continue
            </button>
          </article>
        ))}
      </section>

      <section className="panel access-beta-card">
        <span className="eyebrow">BETA RESERVATION</span>
        <h3>Record interest without collecting payment-card details.</h3>
        <p>
          AgroQ stores the reservation and can send visitors to a hosted payment
          page after a provider is configured.
        </p>
        <button className="button button-primary" onClick={() => open("/beta/reserve")}>
          Reserve beta access
        </button>
      </section>
    </div>
  );
}
