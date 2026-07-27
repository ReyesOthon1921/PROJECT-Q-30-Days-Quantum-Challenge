import {
  BadgeDollarSign,
  Bot,
  BriefcaseBusiness,
  CheckCircle2,
  Database,
  FileCheck2,
  LockKeyhole,
  Scale,
  ShieldCheck,
  Users,
} from "lucide-react";
import "../governance_transparency.css";

const leadership = [
  {
    initials: "OR",
    name: "Othon Reyes Jr.",
    title: "Founder · CEO · Technical Lead",
    scope:
      "Product engineering, technical architecture, research systems, evidence controls, and platform development.",
  },
  {
    initials: "EO",
    name: "Edith Ortiz",
    title: "Co-Founder · Operations Lead",
    scope:
      "Customer discovery, grower relationships, operational planning, workflow research, pilot coordination, and market validation.",
  },
];

const aiDisclosures = [
  ["Application records", "Synthetic demonstration data", "Not live field measurements"],
  ["Commercial visuals", "May include AI-generated concept media", "Not footage of an operating deployment"],
  ["AI recommendations", "Prototype previews requiring human review", "No autonomous agricultural decisions"],
  ["Quantum workspace", "Classical, quantum-inspired, and simulator research", "No quantum-advantage claim"],
  ["Agricultural outcomes", "Research and pilot hypotheses only", "No promised yield, cost, or biological result"],
];

const foundingTerms = [
  ["First 100 approved operations", "$500 proposed first-year rate"],
  ["Approved operations 101–200", "$800 proposed first-year rate"],
  ["After the first 200", "$1,000 planned first-year rate"],
  ["Possible year-two renewal", "$1,500 planned annual rate"],
];

function Notice({ icon: Icon, title, children }) {
  return (
    <article className="governance-notice">
      <div className="governance-icon"><Icon size={20} /></div>
      <div><h3>{title}</h3>{children}</div>
    </article>
  );
}

export default function GovernanceTransparencyPage() {
  return (
    <div className="governance-stack">
      <section className="panel governance-hero">
        <div>
          <span className="eyebrow">Q23–Q25 · Public governance and transparency</span>
          <h1>Built openly. Limited honestly. Led by people.</h1>
          <p>
            AgroQ is an early-stage operating system for agricultural field trials.
            This page identifies the founders, explains how AI and synthetic data
            are used, and preserves the business and research boundaries of the
            public prototype.
          </p>
        </div>
        <div className="governance-hero-badge">
          <ShieldCheck size={34} />
          <strong>Human-reviewed prototype</strong>
          <span>No automatic field control</span>
        </div>
      </section>

      <section className="panel governance-section">
        <div className="governance-heading">
          <Users size={22} />
          <div><span className="eyebrow">Q23 · Leadership</span><h2>Founding team</h2></div>
        </div>
        <div className="founder-grid">
          {leadership.map((person) => (
            <article className="founder-card" key={person.name}>
              <div className="founder-avatar">{person.initials}</div>
              <div>
                <h3>{person.name}</h3>
                <strong>{person.title}</strong>
                <p>{person.scope}</p>
              </div>
            </article>
          ))}
        </div>
        <p className="governance-footnote">
          Titles describe current working responsibilities and do not by themselves
          represent a public securities offering, employment promise, or endorsement.
        </p>
      </section>

      <section className="panel governance-section">
        <div className="governance-heading">
          <Bot size={22} />
          <div><span className="eyebrow">Q24 · AI and evidence transparency</span><h2>What the demonstration means</h2></div>
        </div>
        <div className="disclosure-table" role="table" aria-label="AI and evidence disclosures">
          {aiDisclosures.map(([area, current, boundary]) => (
            <div className="disclosure-row" role="row" key={area}>
              <strong role="cell">{area}</strong>
              <span role="cell">{current}</span>
              <span role="cell">{boundary}</span>
            </div>
          ))}
        </div>
        <div className="governance-callout">
          <FileCheck2 size={20} />
          <p>
            AI-assisted code, writing, and concept media are reviewed by a human
            before publication. Founder names and roles refer to real people.
            Concept visuals do not establish scientific validation or product performance.
          </p>
        </div>
      </section>

      <section className="governance-two-column">
        <section className="panel governance-section">
          <div className="governance-heading">
            <BadgeDollarSign size={22} />
            <div><span className="eyebrow">Q25 · Preliminary offer terms</span><h2>Founding Grower Program</h2></div>
          </div>
          <div className="pricing-list">
            {foundingTerms.map(([group, price]) => (
              <div key={group}><span>{group}</span><strong>{price}</strong></div>
            ))}
          </div>
          <ul className="governance-list">
            <li>Applications are non-binding and do not reserve a position.</li>
            <li>No payment is collected through the public application.</li>
            <li>Eligibility, acceptance, scope, pricing, and benefits require written confirmation.</li>
            <li>No automatic renewal is currently offered.</li>
            <li>Hardware, sensors, laboratory services, travel, installation, integrations, training, and on-site support require a separate written scope.</li>
          </ul>
        </section>

        <section className="panel governance-section">
          <div className="governance-heading">
            <LockKeyhole size={22} />
            <div><span className="eyebrow">Notice at collection</span><h2>Public contact and application data</h2></div>
          </div>
          <div className="privacy-grid">
            <Notice icon={Database} title="Information collected">
              <p>Name, contact details, organization, role, location, operational profile, program interests, and information voluntarily submitted.</p>
            </Notice>
            <Notice icon={BriefcaseBusiness} title="Purposes">
              <p>Respond to requests, review program fit, conduct customer discovery, support pilots, prevent abuse, and maintain auditable records.</p>
            </Notice>
            <Notice icon={ShieldCheck} title="Current data position">
              <p>AgroQ does not state that application data is sold or shared for cross-context behavioral advertising. Protected records require authentication.</p>
            </Notice>
            <Notice icon={FileCheck2} title="Retention">
              <p>Records should be kept only as reasonably necessary for the disclosed purpose, security, evidence preservation, and applicable legal obligations.</p>
            </Notice>
          </div>
          <p className="governance-footnote">
            Contact: reyesothon1921@gmail.com. Privacy rights and obligations depend
            on applicable law and AgroQ's status at the time of a request.
          </p>
        </section>
      </section>

      <section className="panel governance-section">
        <div className="governance-heading">
          <Scale size={22} />
          <div><span className="eyebrow">California-facing safeguards</span><h2>Clear claims and affirmative consent</h2></div>
        </div>
        <div className="safeguard-grid">
          {[
            "Public statements must distinguish prototypes, simulations, research plans, and validated capabilities.",
            "Material pricing, renewal, hardware, availability, and performance terms must be presented before acceptance.",
            "Any future automatic-renewal offer requires clear terms and affirmative consent; none is active today.",
            "Founder voice, image, likeness, and recordings require the participant's permission before commercial publication.",
            "AI-generated concept media must remain labeled when a reasonable viewer could mistake it for real product or field evidence.",
            "Agricultural, biological, environmental, financial, and quantum results are not guaranteed.",
          ].map((item) => (
            <div key={item}><CheckCircle2 size={18} /><span>{item}</span></div>
          ))}
        </div>
        <p className="governance-footnote">
          These safeguards are operational disclosures, not legal advice or a claim
          that every cited California statute applies to AgroQ in every circumstance.
          Terms and privacy practices should be reviewed before paid enrollment.
        </p>
      </section>
    </div>
  );
}
