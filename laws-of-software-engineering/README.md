# Laws of Software Engineering

Catalog of foundational laws, principles, and mental models in software engineering, extracted from [lawsofsoftwareengineering.com](https://lawsofsoftwareengineering.com/).

The laws are organized by theme into individual markdown files:

| Theme | File | Laws | Scope |
|---|---|---|---|
| **Architecture** | [architecture.md](architecture.md) | 9 | System boundaries, abstractions, distributed fallacies |
| **Decisions** | [decisions.md](decisions.md) | 12 | Cognitive biases, mental models, tradeoffs |
| **Design** | [design.md](design.md) | 6 | Code design, coupling, cohesion, SOLID, YAGNI, DRY |
| **Planning** | [planning.md](planning.md) | 6 | Estimation, scope, optimization timing, metrics |
| **Quality** | [quality.md](quality.md) | 11 | Testing, maintenance, technical debt, bugs |
| **Scale** | [scale.md](scale.md) | 3 | Parallelism, network effects, scaling throughput |
| **Teams** | [teams.md](teams.md) | 9 | Human dynamics, communication, organization, productivity |

## Complete Index of Laws (56)

| # | Law | Theme | Level | Summary |
|---|---|---|---|---|
| 1 | [Conway's Law](teams.md#conways-law) | [Teams](teams.md) | Senior | Organizations design systems that mirror their own communication structure. |
| 2 | [Premature Optimization (Knuth's Optimization Principle)](planning.md#premature-optimization) | [Planning](planning.md) | Junior | Premature optimization is the root of all evil. |
| 3 | [Hyrum's Law](architecture.md#hyrums-law) | [Architecture](architecture.md) | Senior | With a sufficient number of API users, all observable behaviors of your system will be depended on by somebody. |
| 4 | [The Boy Scout Rule](quality.md#boy-scout-rule) | [Quality](quality.md) | Junior | Leave the code better than you found it. |
| 5 | [YAGNI (You Aren't Gonna Need It)](design.md#yagni) | [Design](design.md) | Junior | Don't add functionality until it is necessary. |
| 6 | [Brooks's Law](teams.md#brooks-law) | [Teams](teams.md) | Mid | Adding manpower to a late software project makes it later. |
| 7 | [Gall's Law](architecture.md#galls-law) | [Architecture](architecture.md) | Senior | A complex system that works is invariably found to have evolved from a simple system that worked. |
| 8 | [The Law of Leaky Abstractions](architecture.md#law-of-leaky-abstractions) | [Architecture](architecture.md) | Mid | All non-trivial abstractions, to some degree, are leaky. |
| 9 | [Tesler's Law (Conservation of Complexity)](architecture.md#teslers-law) | [Architecture](architecture.md) | Senior | Every application has an inherent amount of irreducible complexity that can only be shifted, not eliminated. |
| 10 | [CAP Theorem](architecture.md#cap-theorem) | [Architecture](architecture.md) | Senior | A distributed system can guarantee only two of: consistency, availability, and partition tolerance. |
| 11 | [Second-System Effect](architecture.md#second-system-effect) | [Architecture](architecture.md) | Senior | Small, successful systems tend to be followed by overengineered, bloated replacements. |
| 12 | [Fallacies of Distributed Computing](architecture.md#fallacies-of-distributed-computing) | [Architecture](architecture.md) | Senior | A set of eight false assumptions that new distributed system designers often make. |
| 13 | [Law of Unintended Consequences](architecture.md#law-of-unintended-consequences) | [Architecture](architecture.md) | Senior | Whenever you change a complex system, expect surprise. |
| 14 | [Zawinski's Law](architecture.md#zawinskis-law) | [Architecture](architecture.md) | Senior | Every program attempts to expand until it can read mail. |
| 15 | [Dunbar's Number](teams.md#dunbars-number) | [Teams](teams.md) | Senior | There is a cognitive limit of about 150 stable relationships one person can maintain. |
| 16 | [The Ringelmann Effect](teams.md#ringelmann-effect) | [Teams](teams.md) | Mid | Individual productivity decreases as group size increases. |
| 17 | [Price's Law](teams.md#prices-law) | [Teams](teams.md) | Senior | The square root of the total number of participants does 50% of the work. |
| 18 | [Putt's Law](teams.md#putts-law) | [Teams](teams.md) | Senior | Those who understand technology don't manage it, and those who manage it don't understand it. |
| 19 | [Peter Principle](teams.md#peter-principle) | [Teams](teams.md) | Mid | In a hierarchy, every employee tends to rise to their level of incompetence. |
| 20 | [Bus Factor](teams.md#bus-factor) | [Teams](teams.md) | Mid | The minimum number of team members whose loss would put the project in serious trouble. |
| 21 | [Dilbert Principle](teams.md#dilbert-principle) | [Teams](teams.md) | Senior | Companies tend to promote incompetent employees to management to limit the damage they can do. |
| 22 | [Parkinson's Law](planning.md#parkinsons-law) | [Planning](planning.md) | Junior | Work expands to fill the time available for its completion. |
| 23 | [The Ninety-Ninety Rule](planning.md#ninety-ninety-rule) | [Planning](planning.md) | Mid | The first 90% of the code accounts for the first 90% of development time; the remaining 10% accounts for the other 90%. |
| 24 | [Hofstadter's Law](planning.md#hofstadters-law) | [Planning](planning.md) | Junior | It always takes longer than you expect, even when you take into account Hofstadter's Law. |
| 25 | [Goodhart's Law](planning.md#goodharts-law) | [Planning](planning.md) | Senior | When a measure becomes a target, it ceases to be a good measure. |
| 26 | [Gilb's Law](planning.md#gilbs-law) | [Planning](planning.md) | Mid | Anything you need to quantify can be measured in some way better than not measuring it. |
| 27 | [Murphy's Law / Sod's Law](quality.md#murphys-law) | [Quality](quality.md) | Junior | Anything that can go wrong will go wrong. |
| 28 | [Postel's Law](quality.md#postels-law) | [Quality](quality.md) | Mid | Be conservative in what you do, be liberal in what you accept from others. |
| 29 | [Broken Windows Theory](quality.md#broken-windows-theory) | [Quality](quality.md) | Mid | Don't leave broken windows (bad designs, wrong decisions, or poor code) unrepaired. |
| 30 | [Technical Debt](quality.md#technical-debt) | [Quality](quality.md) | Junior | Technical Debt is everything that slows us down when developing software. |
| 31 | [Linus's Law](quality.md#linuss-law) | [Quality](quality.md) | Mid | Given enough eyeballs, all bugs are shallow. |
| 32 | [Kernighan's Law](quality.md#kernighans-law) | [Quality](quality.md) | Junior | Debugging is twice as hard as writing the code in the first place. |
| 33 | [Testing Pyramid](quality.md#testing-pyramid) | [Quality](quality.md) | Junior | A project should have many fast unit tests, fewer integration tests, and only a small number of UI tests. |
| 34 | [Pesticide Paradox](quality.md#pesticide-paradox) | [Quality](quality.md) | Mid | Repeatedly running the same tests becomes less effective over time. |
| 35 | [Lehman's Laws of Software Evolution](quality.md#lehmans-laws) | [Quality](quality.md) | Senior | Software that reflects the real world must evolve, and that evolution has predictable limits. |
| 36 | [Sturgeon's Law](quality.md#sturgeons-law) | [Quality](quality.md) | Junior | 90% of everything is crap. |
| 37 | [Amdahl's Law](scale.md#amdahls-law) | [Scale](scale.md) | Senior | The speedup from parallelization is limited by the fraction of work that cannot be parallelized. |
| 38 | [Gustafson's Law](scale.md#gustafsons-law) | [Scale](scale.md) | Senior | It is possible to achieve significant speedup in parallel processing by increasing the problem size. |
| 39 | [Metcalfe's Law](scale.md#metcalfes-law) | [Scale](scale.md) | Senior | The value of a network is proportional to the square of the number of users. |
| 40 | [DRY (Don't Repeat Yourself)](design.md#dry-principle) | [Design](design.md) | Junior | Every piece of knowledge must have a single, unambiguous, authoritative representation. |
| 41 | [KISS (Keep It Simple, Stupid)](design.md#kiss-principle) | [Design](design.md) | Junior | Designs and systems should be as simple as possible. |
| 42 | [SOLID Principles](design.md#solid-principles) | [Design](design.md) | Mid | Five main guidelines that enhance software design, making code more maintainable and scalable. |
| 43 | [Law of Demeter](design.md#law-of-demeter) | [Design](design.md) | Mid | An object should only interact with its immediate friends, not strangers. |
| 44 | [Principle of Least Astonishment](design.md#principle-of-least-astonishment) | [Design](design.md) | Mid | Software and interfaces should behave in a way that least surprises users and other developers. |
| 45 | [Dunning-Kruger Effect](decisions.md#dunning-kruger-effect) | [Decisions](decisions.md) | Junior | The less you know about something, the more confident you tend to be. |
| 46 | [Hanlon's Razor](decisions.md#hanlons-razor) | [Decisions](decisions.md) | Junior | Never attribute to malice that which is adequately explained by stupidity or carelessness. |
| 47 | [Occam's Razor](decisions.md#occams-razor) | [Decisions](decisions.md) | Junior | The simplest explanation is often the most accurate one. |
| 48 | [Sunk Cost Fallacy](decisions.md#sunk-cost-fallacy) | [Decisions](decisions.md) | Mid | Sticking with a choice because you've invested time or energy in it, even when walking away helps you. |
| 49 | [The Map Is Not the Territory](decisions.md#map-is-not-the-territory) | [Decisions](decisions.md) | Mid | Our representations of reality are not the same as reality itself. |
| 50 | [Confirmation Bias](decisions.md#confirmation-bias) | [Decisions](decisions.md) | Mid | A tendency to favor information that supports our existing beliefs or ideas. |
| 51 | [The Hype Cycle & Amara's Law](decisions.md#hype-cycle-amaras-law) | [Decisions](decisions.md) | Mid | We tend to overestimate the effect of a technology in the short run and underestimate the impact in the long run. |
| 52 | [The Lindy Effect](decisions.md#lindy-effect) | [Decisions](decisions.md) | Mid | The longer something has been in use, the more likely it is to continue being used. |
| 53 | [First Principles Thinking](decisions.md#first-principles-thinking) | [Decisions](decisions.md) | Mid | Breaking a complex problem into its most basic blocks and then building up from there. |
| 54 | [Inversion](decisions.md#inversion) | [Decisions](decisions.md) | Mid | Solving a problem by considering the opposite outcome and working backward from it. |
| 55 | [Pareto Principle (80/20 Rule)](decisions.md#pareto-principle) | [Decisions](decisions.md) | Junior | 80% of the problems result from 20% of the causes. |
| 56 | [Cunningham's Law](decisions.md#cunninghams-law) | [Decisions](decisions.md) | Junior | The best way to get the correct answer on the Internet is not to ask a question, it's to post the wrong answer. |

---

Extracted automatically with key takeaways, overviews, examples, historical origins, further reading, and cross-references.
