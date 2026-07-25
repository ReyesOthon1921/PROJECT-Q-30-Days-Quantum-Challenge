import {
  Atom,
  BookOpen,
  Code2,
  Cpu,
  ExternalLink,
  GraduationCap,
  Heart,
  Leaf,
  Network,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";

const researchGroups = [
  {
    id: "soil",
    eyebrow: "Soil biology and living systems",
    icon: Leaf,
    description:
      "Research that helped shape AgroQ's view of soil as a living biological network rather than a chemistry-only system.",
    people: [
      {
        name: "Dr. Elaine R. Ingham",
        role: "Soil microbial ecology and Soil Food Web research",
        contribution:
          "Research on bacteria, fungi, protozoa, nematodes, mycorrhizae, decomposition, nutrient cycling, and soil-food-web structure informed the Soil Biology module.",
        sourceLabel: "Publication list",
        sourceUrl: "https://soilfoodweb.com/publications/",
      },
    ],
  },
  {
    id: "quantum",
    eyebrow: "Quantum and hybrid optimization",
    icon: Atom,
    description:
      "Foundational and project-specific work that informs the quantum research lane, comparison discipline, and decision-optimization concepts.",
    people: [
      {
        name: "Edward Farhi, Jeffrey Goldstone, and Sam Gutmann",
        role: "Quantum Approximate Optimization Algorithm",
        contribution:
          "Their QAOA work is acknowledged as a foundational reference for quantum approximate optimization and matched classical-versus-quantum comparison.",
        sourceLabel: "Original QAOA paper",
        sourceUrl: "https://arxiv.org/abs/1411.4028",
      },
      {
        name: "Shlok Goenka, Chaitanya Upadhyay, Veer Jain, and Suresh Kumar Jha",
        role: "QAMR research authors referenced in project planning",
        contribution:
          "Their quantum-network decision and optimization research helped expand the founder's thinking about quantum-assisted routing, resource decisions, and network-level optimization.",
        sourceLabel: "Founder-provided attribution",
        sourceUrl: null,
        note:
          "The final public paper link and citation metadata should be verified before a formal publication or investor appendix is released.",
      },
    ],
  },
  {
    id: "classical",
    eyebrow: "Classical optimization and benchmarking",
    icon: Network,
    description:
      "Classical methods remain the baseline and evidence standard for every quantum or quantum-inspired result presented by AgroQ.",
    people: [
      {
        name: "S. Kirkpatrick, C. D. Gelatt Jr., and M. P. Vecchi",
        role: "Simulated annealing",
        contribution:
          "Their simulated-annealing work is acknowledged as a foundation for classical heuristic optimization and equal-budget baseline comparisons.",
        sourceLabel: "Original publication",
        sourceUrl: "https://doi.org/10.1126/science.220.4598.671",
      },
      {
        name: "Classical graph, statistical, and optimization research communities",
        role: "Graphs, Laplacian methods, controls, calibration, and uncertainty",
        contribution:
          "AgroQ uses graph-based reasoning, controls versus treatments, calibration, anomaly scoring, and uncertainty-aware sampling as research tools. Each production claim must be tied to a specific source and validated dataset.",
        sourceLabel: "Source registry required",
        sourceUrl: null,
      },
    ],
  },
];

const engineeringCredits = [
  {
    name: "React and Vite contributors",
    detail: "Frontend component system and production build tooling.",
  },
  {
    name: "Flask and Python contributors",
    detail: "Backend application, routes, research workflows, and service integration.",
  },
  {
    name: "SQLite contributors",
    detail: "Local-first data storage and auditable prototype records.",
  },
  {
    name: "Three.js and React Three Fiber contributors",
    detail: "Interactive 3D Digital Acre visualization.",
  },
  {
    name: "Framer Motion and Lucide contributors",
    detail: "Interface motion and accessible visual iconography.",
  },
  {
    name: "Qiskit and the IBM Quantum open-source community",
    detail: "Quantum-circuit education, simulation, and research experimentation.",
  },
];

const founderAcknowledgments = [
  {
    name: "Edith Ortiz",
    role: "Co-founder and operations partner",
    thanks:
      "For long-term support, operational perspective, healthcare experience, customer discovery, and helping turn the founder's research direction into a company-building path.",
  },
  {
    name: "Christian St Louis",
    role: "Research collaborator, mathematical thinking, and encouragement",
    thanks:
      "For helping the founder work through mathematical ideas, sharing research perspectives, encouraging the project, and approaching the work with a genuine spirit of collaboration.",
  },
  {
    name: "Professor Parisa Samadi",
    role: "Academic guidance",
    thanks:
      "Acknowledged for guidance within the founder's computer-science and research-development journey.",
  },
  {
    name: "Professor Bindu Chandra Shekar Reddy",
    role: "Academic and research guidance",
    thanks:
      "Acknowledged for guidance connected to the founder's technical and research development.",
  },
  {
    name: "Dr. Valerie Herrington",
    role: "Quantum education and community guidance",
    thanks:
      "Acknowledged for support and guidance connected to QWorld and quantum-community development.",
  },
  {
    name: "Krishna Bhatia and Shalini Devendrababu",
    role: "Quantum project mentorship",
    thanks:
      "Acknowledged for mentorship connected to the founder's quantum research and project work.",
  },
  {
    name: "WISER, QWorld/QCousins, Sacramento State, and the broader learning community",
    role: "Programs, educators, peers, and collaborators",
    thanks:
      "Thank you to the people who supplied instruction, feedback, challenge problems, research discussions, and opportunities to learn by building.",
  },
];

function SourceLink({ label, url }) {
  if (!url) {
    return <span className="credit-source credit-source-pending">{label}</span>;
  }

  return (
    <a className="credit-source" href={url} target="_blank" rel="noreferrer">
      {label}
      <ExternalLink size={14} />
    </a>
  );
}

export default function ResearchCreditsPage() {
  return (
    <div className="page-stack research-credits-page">
      <section className="credits-hero panel">
        <div className="credits-hero-icon">
          <Heart size={34} />
        </div>
        <div>
          <span className="eyebrow">Research, attribution, and gratitude</span>
          <h1>Built with ideas from many people</h1>
          <p>
            AgroQ is founder-led, but it is not intellectually isolated. This page
            recognizes the researchers, authors, mentors, collaborators, programs, and
            open-source communities whose work helped shape the platform.
          </p>
        </div>
      </section>

      <section className="credits-integrity panel">
        <ShieldCheck size={24} />
        <div>
          <h2>Attribution policy</h2>
          <p>
            Credit means intellectual influence, education, mentorship, collaboration,
            or software contribution. It does not imply employment, partnership,
            sponsorship, affiliation, approval, or endorsement of AgroQ unless a written
            agreement says otherwise. Citations marked for verification must be checked
            before formal publication.
          </p>
        </div>
      </section>

      <section className="credits-research-stack">
        {researchGroups.map(({ id, eyebrow, icon: Icon, description, people }) => (
          <article className="panel credits-research-section" key={id}>
            <div className="credits-section-heading">
              <div className="credits-section-icon">
                <Icon size={22} />
              </div>
              <div>
                <span>{eyebrow}</span>
                <p>{description}</p>
              </div>
            </div>

            <div className="credits-people-grid">
              {people.map((person) => (
                <div className="credit-person-card" key={person.name}>
                  <div>
                    <h3>{person.name}</h3>
                    <strong>{person.role}</strong>
                  </div>
                  <p>{person.contribution}</p>
                  {person.note && <div className="credit-note">{person.note}</div>}
                  <SourceLink label={person.sourceLabel} url={person.sourceUrl} />
                </div>
              ))}
            </div>
          </article>
        ))}
      </section>

      <section className="panel credits-engineering-section">
        <div className="credits-title-row">
          <div>
            <span className="eyebrow">Open-source engineering</span>
            <h2>Tools and contributor communities</h2>
          </div>
          <Code2 size={28} />
        </div>

        <div className="credits-engineering-grid">
          {engineeringCredits.map((credit) => (
            <div key={credit.name}>
              <Cpu size={18} />
              <span>
                <strong>{credit.name}</strong>
                <small>{credit.detail}</small>
              </span>
            </div>
          ))}
        </div>
      </section>

      <section className="panel credits-thanks-section">
        <div className="credits-title-row">
          <div>
            <span className="eyebrow">Founder's acknowledgments</span>
            <h2>Thank you for helping build the path</h2>
          </div>
          <GraduationCap size={30} />
        </div>

        <div className="credits-thanks-grid">
          {founderAcknowledgments.map((entry) => (
            <article key={entry.name}>
              <div className="credits-avatar">
                {entry.name
                  .split(" ")
                  .slice(0, 2)
                  .map((part) => part[0])
                  .join("")}
              </div>
              <div>
                <h3>{entry.name}</h3>
                <strong>{entry.role}</strong>
                <p>{entry.thanks}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="credits-founder-note panel">
        <Sparkles size={26} />
        <div>
          <span>A note from the founder</span>
          <blockquote>
            “Thank you to every researcher, teacher, mentor, collaborator, family member,
            and open-source contributor whose work helped me turn years of ideas,
            experiments, questions, and belief into something visible. AgroQ will keep
            improving its citations and giving credit as the platform grows.”
          </blockquote>
          <strong>— Othon Reyes Jr., Founder and Research Lead</strong>
        </div>
      </section>

      <section className="credits-maintenance panel">
        <BookOpen size={23} />
        <div>
          <h2>Living credit registry</h2>
          <p>
            This page should be updated whenever AgroQ adopts a new paper, dataset,
            algorithm, protocol, mentorship contribution, collaborator deliverable, or
            open-source dependency. Corrections should be made promptly and respectfully.
          </p>
        </div>
        <div className="credits-maintenance-tags">
          <span>Research sources</span>
          <span>Algorithm authors</span>
          <span>Mentors</span>
          <span>Collaborators</span>
          <span>Open source</span>
        </div>
      </section>
    </div>
  );
}
