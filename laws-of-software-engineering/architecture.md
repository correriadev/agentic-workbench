# Laws of Software Engineering — Architecture

Extracted from [Laws of Software Engineering](https://lawsofsoftwareengineering.com/). This document covers all **9** principles categorized under **Architecture**.

## Table of Contents

- [Hyrum's Law](#hyrums-law) — *With a sufficient number of API users, all observable behaviors of your system will be depended on by somebody.* (Senior)
- [Gall's Law](#galls-law) — *A complex system that works is invariably found to have evolved from a simple system that worked.* (Senior)
- [The Law of Leaky Abstractions](#law-of-leaky-abstractions) — *All non-trivial abstractions, to some degree, are leaky.* (Mid)
- [Tesler's Law (Conservation of Complexity)](#teslers-law) — *Every application has an inherent amount of irreducible complexity that can only be shifted, not eliminated.* (Senior)
- [CAP Theorem](#cap-theorem) — *A distributed system can guarantee only two of: consistency, availability, and partition tolerance.* (Senior)
- [Second-System Effect](#second-system-effect) — *Small, successful systems tend to be followed by overengineered, bloated replacements.* (Senior)
- [Fallacies of Distributed Computing](#fallacies-of-distributed-computing) — *A set of eight false assumptions that new distributed system designers often make.* (Senior)
- [Law of Unintended Consequences](#law-of-unintended-consequences) — *Whenever you change a complex system, expect surprise.* (Senior)
- [Zawinski's Law](#zawinskis-law) — *Every program attempts to expand until it can read mail.* (Senior)

---

<a id="hyrums-law"></a>
## Hyrum's Law

> **Category:** Architecture | **Level:** Senior | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/hyrums-law/](https://lawsofsoftwareengineering.com/laws/hyrums-law/)

**With a sufficient number of API users, all observable behaviors of your system will be depended on by somebody.**

### Key Takeaways

- As the user count grows, everything your system does becomes a dependency point. Even unintended side effects or bugs can become ‘features’ that someone’s workflow depends on.
- Hyrum’s Law warns maintainers that any change can break something for someone. Consumers may have integrated your API in ways you didn’t expect, including relying on timing, error messages, formatting, etc.
- The actual contract of your software isn’t just the official API/spec; it’s the exact behavior as observed in the wild. The contract can even be something informal, such as the UI that your users are used to.

### Overview

Hyrum’s Law describes a phenomenon where the boundary between a software’s documented interface and its implementation details gets blurred in practice. No matter what you promise in an API contract, if people use your system enough, they will depend on behaviors you never officially supported.

Over time, the implementation becomes the interface. Every observable trait, performance characteristic, or error code might be assumed by someone. This drastically limits freedom to change the system, as even internal changes can break users who wrote code around the old behavior.

### Examples

**Microsoft Windows** had undocumented behaviors and bugs that many third-party applications relied on. When Microsoft fixed or changed those behaviors in new versions, those applications broke. Microsoft often had to revert or maintain quirky behavior to ensure compatibility.

A **library** might state in the docs that a function returns an unordered list, but it currently returns a sorted list. Some users start depending on it being sorted. If the library later changes to truly unordered, those users’ code will break. The law is especially relevant in API versioning: even minor changes can be breaking changes from someone’s perspective.

### Origins

The law is named after **Hyrum Wright**, a software engineer who articulated this observation while at Google around 2011-2012. Hyrum noticed that even changes to core Google libraries that should have been invisible would often break some project somewhere, because that project relied on an undocumented behavior.

His colleague, Titus Winters, coined the term “Hyrum’s Law” in recognition of it (in Software Engineering at Google).

### Further Reading

- [Hyrum's Law Official Site](https://www.hyrumslaw.com/) — The official explanation of Hyrum's Law
- [Software Engineering at Google](https://abseil.io/resources/swe-book/html/ch01.html#hyrumapostrophes_law) — Discusses Hyrum's Law in the context of large-scale systems
- [Hyrum's Law on xkcd](https://xkcd.com/1172/) — Comic illustrating the problem

### Related Laws

- [The Law of Leaky Abstractions](#law-of-leaky-abstractions)

---

<a id="galls-law"></a>
## Gall's Law

> **Category:** Architecture | **Level:** Senior | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/galls-law/](https://lawsofsoftwareengineering.com/laws/galls-law/)

**A complex system that works is invariably found to have evolved from a simple system that worked.**

### Key Takeaways

- Don’t build a complex system from scratch. Instead, make a simple version that works, then iterate and add complexity. This approach serves as a launching pad for experimentation and innovation.
- Successful large systems often grow organically. A fully designed-from-scratch complex system usually fails because you can’t foresee all interactions.
- This law argues for creating a Minimum Viable Product (MVP), a simple working core, and then growing it, rather than a big-bang approach.
- Systems that grow tend to adapt and handle complexity better because they’ve been tested and refined at each stage. An overly complex initial design can break when something unexpected happens.

### Overview

John Gall observed that **successful complex systems start as successful simple systems**. If you attempt to create a complex system from the beginning, it usually doesn’t work because there are too many unknowns you haven’t validated.

Instead, start with a simple architecture and learn from real-world usage. Add features or complexity incrementally, ensuring each change still works. When you start with a small, functional core, you can validate assumptions early. Every new capability added incrementally is tested against reality, forcing the system to adapt.

### Examples

**Facebook** started as a simple website for Harvard students. It was essentially a basic user profile system that worked at that small scale, then expanded gradually, adding features and handling more users. If Mark Zuckerberg had tried to build today’s Facebook from scratch in 2004, it would almost certainly have collapsed under its own complexity.

In the era of microservices, a common piece of advice influenced by Gall’s Law is: don’t start with microservices. Start with a monolith (a simpler architecture) that works. As it grows, identify pieces to split off into separate services. Those pieces have the benefit of prior existence, you know their requirements from the monolith, and thus are more likely to work once isolated.

### Origins

**John Gall**, an American pediatrician with a sideline in systems theory, published *Systemantics: How Systems Work and Especially How They Fail* in 1975. 30 publishers initially rejected the book before it became a cult classic.

The third edition (2002) of the book is named *The Systems Bible*.

### Further Reading

- [The Systems Bible](https://amzn.to/4svZT0K) — John Gall
- [The Mythical Man-Month](https://amzn.to/4b4GU72) — Fred Brooks
- [Monolith First](https://martinfowler.com/bliki/MonolithFirst.html) — Martin Fowler
- [Thinking in Systems](https://amzn.to/4qgVSvH) — Donella Meadows' primer on systems thinking and complexity

### Related Laws

- [Conway's Law](teams.md#conways-law)
- [Brooks's Law](teams.md#brooks-law)
- [The Law of Leaky Abstractions](#law-of-leaky-abstractions)
- [Hofstadter's Law](planning.md#hofstadters-law)

---

<a id="law-of-leaky-abstractions"></a>
## The Law of Leaky Abstractions

> **Category:** Architecture | **Level:** Mid | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/law-of-leaky-abstractions/](https://lawsofsoftwareengineering.com/laws/law-of-leaky-abstractions/)

**All non-trivial abstractions, to some degree, are leaky.**

### Key Takeaways

- No matter how well-designed, abstractions (libraries, frameworks, etc.) have edge cases that depend on internal details.
- Developers should understand that using a high-level tool doesn’t absolve them from knowing what’s happening underneath, at least at a basic level.
- “Leaky” means you might encounter performance issues, bugs, or behavior that force you to consider the underlying system (e.g., networking, OS) on which the abstraction sits.
- When creating abstractions, strive to minimize leakage and document the cases in which it might break.

### Overview

This law observes that in complex systems, the abstractions we create, meant to hide complexity, *inevitably fail in some scenarios*, revealing the underlying complexity to the programmer.

For example, consider an ORM (object-relational mapper) that lets you treat database entries as objects. Most of the time it works, but occasionally you hit a case where performance is terrible and you have to think about the SQL queries being generated. The abstraction “leaks” details of the database.

The law isn’t saying abstractions are bad. They are essential. But it reminds us that **one must be prepared for when they break**.

### Examples

A good example is **memory management in high-level languages**. Languages like Java and Python abstract away manual memory allocation thanks to garbage collection. Yet leaks still happen (objects not being freed due to lingering references), or you encounter the abstraction’s limits (such as GC pauses affecting performance). Suddenly, the developer needs to know how garbage collection works internally, and the abstraction of “infinite memory” has leaked.

Web developers often treat an HTTP request as something fast, abstracting away the network. However, when latency spikes or packets drop, the network’s reality leaks into your application.

### Origins

Joel Spolsky introduced this law in a 2002 blog post. He gave examples such as TCP (which abstracts reliable connections over IP, but on a bad network the abstraction leaks, causing timeouts) or the virtual memory abstraction.

The concept resonates with many earlier thoughts in computing, essentially a restatement of “there’s no free lunch” with abstractions.

### Further Reading

- [The Law of Leaky Abstractions](https://www.joelonsoftware.com/2002/11/11/the-law-of-leaky-abstractions/) — Joel Spolsky's original blog post
- [A Note on Distributed Computing](https://scholar.harvard.edu/waldo/publications/note-distributed-computing) — Fallacies of Distributed Systems
- [Towards a New Model of Abstraction in Software Engineering](https://web.archive.org/web/20110604013045/http://www2.parc.com/csl/groups/sda/publications/papers/Kiczales-IMSA92/for-web.pdf) — Gregor Kiczales' foundational paper on open implementations and abstraction leakage

### Related Laws

- [Hyrum's Law](#hyrums-law)
- [Gall's Law](#galls-law)

---

<a id="teslers-law"></a>
## Tesler's Law (Conservation of Complexity)

> **Category:** Architecture | **Level:** Senior | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/teslers-law/](https://lawsofsoftwareengineering.com/laws/teslers-law/)

**Every application has an inherent amount of irreducible complexity that can only be shifted, not eliminated.**

### Key Takeaways

- Good design often requires that developers absorb most of the complexity (through smart defaults, algorithms, etc.) so that the user’s interaction is simpler.
- If your UI requires the user to manage many settings or steps, you’ve conserved complexity in the wrong place (on the user side). Often, it’s better to design the product to manage that complexity internally.
- Good design often hides complexity without eliminating it by handling it internally.

### Overview

Tesler’s Law, also known as the Law of Conservation of Complexity, states that for any system, there is a certain amount of complexity that cannot be removed; it’s inherent to the problem. The key is **who deals with it**.

If you design software that’s very simple for the user, it likely means the software is doing a lot of complex work under the hood. If you make the software very simple internally, it might dump complexity on the user (e.g., requiring many manual steps).

Tesler’s Law encourages designers to **move complexity away from the user experience** whenever possible.

### Examples

A classic example is **scheduling meetings**, which is inherently complex (finding a common time). A tool like Calendly hides that complexity from the user (the software handles it), whereas an email chain to schedule a meeting places that complexity on the user to figure out.

In system architecture, imagine designing a database vs. putting logic in application code. Sometimes pushing logic into the DB (such as stored procedures) can simplify app code but add complexity to the DB layer, or vice versa. Complexity isn’t gone, just relocated.

In the end, the law reminds us that no design is without complexity. It’s all about smartly allocating complexity to the right place.

### Further Reading

- [Why Life Can't Be Simpler](https://fs.blog/why-life-cant-be-simpler/) — Farnam Street on the conservation of complexity
- [Law of Conservation of Complexity](https://humanist.co/blog/law-of-conservation-of-complexity/) — Deep dive into Tesler's Law and its implications
- [Simplicity is Overrated](https://marvelapp.com/blog/simplicity-is-overrated/) — Why chasing simplicity isn't always the answer
- [Law of Conservation of Complexity (Wikipedia)](https://en.wikipedia.org/wiki/Law_of_conservation_of_complexity) — Wikipedia article on Tesler's Law

### Related Laws

- [Hyrum's Law](#hyrums-law)
- [Occam's Razor](decisions.md#occams-razor)

---

<a id="cap-theorem"></a>
## CAP Theorem

> **Category:** Architecture | **Level:** Senior | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/cap-theorem/](https://lawsofsoftwareengineering.com/laws/cap-theorem/)

**A distributed system can guarantee only two of: consistency, availability, and partition tolerance.**

### Key Takeaways

- A distributed system can only guarantee two out of three things at once: Consistency, Availability, and Partition Tolerance. When the network is healthy you can have all three, but the moment a partition happens, you have to give one up.
- When a network split occurs, you face a choice: stay consistent (every node agrees, but some requests may fail) or stay available (every request gets an answer, but the data might be slightly out of date). You can’t fully have both.
- Real databases pick a side. MongoDB leans toward consistency, blocking writes during a partition so all replicas stay in sync. Cassandra leans toward availability, keeping the lights on and serving queries even if replicas briefly disagree.

### Overview

The CAP theorem states that a distributed system cannot simultaneously provide all three guarantees: **Consistency** (all nodes see the same data), **Availability** (every request receives a response), and **Partition Tolerance** (the system operates despite network failures).

Since network partitions are unavoidable in practice, systems must be partition-tolerant. This means choosing between consistency and availability when designing distributed architectures. The CAP theorem is a useful starting point, though it is a simplification that doesn’t cover all aspects of the design space.

### Examples

The **Domain Name System (DNS)** is designed as AP (Available and Partition-tolerant). If some name servers are partitioned, they still reply (availability), even if their information might be slightly outdated until zones sync up.

**MongoDB** is a CP (Consistent and Partition-Tolerant) database, blocking writes during a partition so all replicas stay in sync. **Cassandra** is an AP (Available and Partition-Tolerant) database, serving queries even if replicas briefly disagree.

### Origins

Eric Brewer created the theorem in 2000 in the context of web services, and it was later formalized by Gilbert and Lynch in 2002. Brewer observed that designers of large-scale systems faced three concerns: keeping data consistent across nodes, keeping the service up, and handling network unreliability.

The formal proof showed that in a distributed system with shared data, you **must sacrifice either consistency or availability when a network partition occurs**. CAP became a guiding principle in the NoSQL movement and distributed database design in the 2000s.

### Further Reading

- [Brewer's CAP Theorem](https://www.infoq.com/articles/cap-twelve-years-later-how-the-rules-have-changed/) — Eric Brewer's reflection on CAP, twelve years later
- [CAP Twelve Years Later: How the 'Rules' Have Changed](https://sites.cs.ucsb.edu/~rich/class/cs293b-cloud/papers/brewer-cap.pdf) — Brewer's 2012 IEEE paper revisiting and refining the CAP theorem
- [Gilbert & Lynch 2002 Paper](https://groups.csail.mit.edu/tds/papers/Gilbert/Brewer2.pdf) — The formal proof of the CAP theorem
- [Designing Data-Intensive Applications](https://amzn.to/4pVAwU5) — Martin Kleppmann's comprehensive guide covering CAP and distributed systems
- [A Critique of the CAP Theorem](https://www.cl.cam.ac.uk/research/dtg/archived/files/publications/public/mk428/cap-critique.pdf) — Martin Kleppmann's 2015 paper arguing the theorem's definitions are ambiguous

### Related Laws

- [Fallacies of Distributed Computing](#fallacies-of-distributed-computing)

---

<a id="second-system-effect"></a>
## Second-System Effect

> **Category:** Architecture | **Level:** Senior | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/second-system-effect/](https://lawsofsoftwareengineering.com/laws/second-system-effect/)

**Small, successful systems tend to be followed by overengineered, bloated replacements.**

### Key Takeaways

- The first system is kept lean by constraints or inexperience. When designing its successor, there’s a tendency to incorporate all the extras initially left out, leading to feature bloat.
- Overconfidence plays a role. Having succeeded once, the team feels they can tackle much more, underestimating complexity.
- The second-system effect often results in over-engineering with more modules, generality, and features than necessary, hurting performance and maintainability.

### Overview

A small, elegant system is built and works well. A second version is initiated, and the designers, freed from the constraints of the first project, try to build something much bigger and more complex. They add enhancements, address all edge cases, and incorporate wishlist features. The result is often an overly complex, behind-schedule system.

Brooks noted this with IBM’s OS/360: simpler earlier systems were followed by a second system that became very complex. The syndrome is an exercise in hubris. The team doesn’t realize how much harder the bigger scope will be.

The second-system effect warns engineers to be suspicious of grand redesigns that promise to include everything.

### Examples

A startup builds a minimal web service that’s very successful. For version 2, the team plans a complete rewrite with microservice architecture, tons of configuration options, plug-in frameworks, and features users never asked for. The project explodes in complexity and misses deadlines.

**Netscape Navigator** in the 1990s decided to rewrite their browser after initial success, leading to the Mozilla Suite. The rewrite took many years, during which Internet Explorer caught up. The new suite was considered overly complicated, and Netscape lost its lead.

### Origins

Fred Brooks coined the term in 1975 in *The Mythical Man-Month*. He observed it in practice at IBM, where successful small systems (such as simplistic tape-based OS) were followed by OSes that tried to do far more and ran late or failed.

The phrase “second-system syndrome” appears in an essay of the same name in the book.

### Further Reading

- [The Mythical Man-Month](https://amzn.to/4b4GU72) — Fred Brooks' classic book on software engineering
- [Second-system effect - Wikipedia](https://en.wikipedia.org/wiki/Second-system_effect) — Wikipedia article on the Second-system effect
- [Things You Should Never Do, Part I](https://www.joelonsoftware.com/2000/04/06/things-you-should-never-do-part-i/) — Joel Spolsky on the Netscape rewrite disaster

### Related Laws

- [YAGNI (You Aren't Gonna Need It)](design.md#yagni)
- [Gall's Law](#galls-law)
- [Brooks's Law](teams.md#brooks-law)

---

<a id="fallacies-of-distributed-computing"></a>
## Fallacies of Distributed Computing

> **Category:** Architecture | **Level:** Senior | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/fallacies-of-distributed-computing/](https://lawsofsoftwareengineering.com/laws/fallacies-of-distributed-computing/)

**A set of eight false assumptions that new distributed system designers often make.**

### Key Takeaways

- Networks drop messages, introduce delays, have finite throughput, and can be insecure. Properly built distributed systems must account for these with retries, timeouts, security measures, and dynamic discovery.
- The fallacies often manifest in subtle bugs. Assuming latency is zero might lead to chatty remote calls that work fine locally but become painfully slow over a network.
- Taking these fallacies into account leads to defensive design: using caches (bandwidth/latency aren’t perfect), building redundancy (networks aren’t reliable), and handling dynamic membership (topology changes).

### Overview

The Eight Fallacies serve as a checklist of what not to assume. They all spring from treating a distributed system like a local one. Developers might write code as if calling a remote service is just like calling a local function, ignoring latency and failure.

These mistaken assumptions lead to serious issues: unhandled errors when the network breaks, poor performance due to ignoring latency, security breaches from failing to authenticate remote calls.

By calling them “fallacies,” creators sought to instill the mindset that the network will fail and behave non-ideally, so your system must be designed to tolerate that.

### Examples

A developer building a distributed caching system assumes “network latency is zero.” They design the cache to fetch data from a remote node for every lookup. In practice, it thrashes with high latency and poor performance.

A system assumes “the network is secure” and sends sensitive data unencrypted or doesn’t validate inputs from other services. This leads to breaches if the network is compromised. Not planning for changing topology has broken systems when machines are added or removed unexpectedly.

### Origins

Credited primarily to **L. Peter Deutsch** (with others like James Gosling adding to the list) around 1994 at Sun Microsystems. Initially there were seven fallacies; an eighth (“the network is homogeneous”) was added by Gosling later.

Deutsch observed that many engineers, especially those used to local computing, would subconsciously assume the network just works. Formalizing these assumptions as a list helped teams remember to address each one.

### Further Reading

- [Fallacies of Distributed Computing - Wikipedia](https://en.wikipedia.org/wiki/Fallacies_of_distributed_computing) — Wikipedia article on the eight fallacies
- [Fallacies of Distributed Computing Explained](https://www.rgoarchitects.com/Files/fallacies.pdf) — Arnon Rotem-Gal-Oz's detailed explanation of each fallacy
- [The Eight Fallacies of Distributed Computing](https://nighthacks.com/jag/res/Fallacies.html) — James Gosling's page on the fallacies
- [Designing Data-Intensive Applications](https://amzn.to/4pVAwU5) — Martin Kleppmann's book addressing all eight fallacies in depth
- [Foraging for the Fallacies of Distributed Computing](https://medium.com/baseds/foraging-for-the-fallacies-of-distributed-computing-part-1-1b35c3b85b53) — Vaidehi Joshi's accessible explanation of each fallacy

### Related Laws

- [CAP Theorem](#cap-theorem)
- [Murphy's Law / Sod's Law](quality.md#murphys-law)

---

<a id="law-of-unintended-consequences"></a>
## Law of Unintended Consequences

> **Category:** Architecture | **Level:** Senior | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/law-of-unintended-consequences/](https://lawsofsoftwareengineering.com/laws/law-of-unintended-consequences/)

**Whenever you change a complex system, expect surprise.**

### Key Takeaways

- No matter how well you plan, any significant change in a complex system can produce results you cannot anticipate.
- Consequences can be unexpected benefits (happy surprises), unexpected drawbacks (side effects that hinder), or perverse results (the action makes the original problem worse).
- In software engineering, this often manifests as a fix or new feature introducing bugs or performance issues elsewhere.

### Overview

The Law of Unintended Consequences states that outcomes are not entirely predictable. Systems have complex interdependencies and human factors that can cause surprises.

Adding a new feature might unexpectedly degrade performance due to its interaction with an unrelated module. Simplifying a UI could lead to heavier backend load because users use the feature more often than expected.

It reminds engineers that systems are complex and our mental models are incomplete. When implementing changes, anticipate that “unknown unknowns” will crop up.

### Examples

Enabling a new logging feature to help with debugging might fill the disk and crash the system, a perverse result relative to the goal of stability.

A social network changes its algorithm to boost user engagement, but as an unintended consequence, it amplifies outrage or misinformation. A bug fix in one part of the code unexpectedly causes a regression in another module that depended on the original bug behavior (overlap with Hyrum’s Law).

### Origins

Sociologist **Robert K. Merton** popularized the term in the 20th century, though the concept dates back further. In a computing context, it’s more of a borrowed concept than a specific person’s law.

Merton identified five sources of unanticipated consequences: ignorance, error, immediate interest, basic values, and self-defeating prophecy.

### Further Reading

- [Unintended consequences - Wikipedia](https://en.wikipedia.org/wiki/Unintended_consequences) — Wikipedia article on unintended consequences
- [The Unanticipated Consequences of Purposive Social Action](https://www.jstor.org/stable/2084615) — Robert K. Merton's original 1936 paper
- [Freakonomics](https://freakonomics.com/) — Popular economics blog and book series exploring unintended consequences

### Related Laws

- [Hyrum's Law](#hyrums-law)
- [Gall's Law](#galls-law)

---

<a id="zawinskis-law"></a>
## Zawinski's Law

> **Category:** Architecture | **Level:** Senior | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/zawinskis-law/](https://lawsofsoftwareengineering.com/laws/zawinskis-law/)

**Every program attempts to expand until it can read mail.**

### Key Takeaways

- Feature creep is unavoidable. Over time, software tends to accumulate more features, leading to software bloat.
- A lean, minimal application that gains popularity will continually add features until it becomes as complex as its competitors.
- Programs expand because users (and product managers) keep asking for ‘just one more feature’. There is constant pressure to incorporate popular capabilities to keep users from leaving for other tools.
- Each new feature increases complexity, which makes the product confusing for users. Developers should protect the tool’s focus and resist platform sprawl.

### Overview

Zawinski’s Law is a humorous observation about software evolution stating that applications continually gain features until they do everything, even things completely outside their original scope. It highlights feature creep, the gradual expansion of scope in software development.

As an application attracts more users, it faces growing expectations to add more capabilities. A basic note-taking app might later incorporate chat or sharing.

Zawinski’s point was about “platformization”: once users live in an app for a significant part of their day, there is pressure for that app to become a platform that can do everything. Unchecked expansion can sabotage a product’s original value. Adding features is easy, but adding only the right features and saying “no” to the rest is essential.

### Examples

**Netscape Navigator** grew from a slim browser into Netscape Communicator, an expansive suite with browser, email, news, and web editing. It became sluggish and over-complicated, paving the way for Firefox, which deliberately stripped down to just a fast browser. Firefox itself later became heavier with plugins and themes.

**Slack** set out to “kill email” but integrated voice calls, video meetings, file sharing, bots, and app plugins. It now wants to be a one-stop workplace hub, far beyond simple messaging.

**GitHub** started hosting code, then expanded to issue tracking, wikis, project boards, discussions, CI pipelines, and package registries.

### Origins

**Jamie Zawinski** (known as jwz) formulated this law around 1995 during his time at Netscape. He was a key programmer on Netscape Navigator and later added the integrated Netscape Mail reader.

He described the browser’s evolution as “our contribution to the proof of the Law of Software Envelopment.” Netscape started as a web browser but by version 2.0-3.0 had expanded to include an email client and news reader.

“Reading mail” was the chosen example because in the mid-90s, you often had to exit your current application and launch a mail program separately.

### Further Reading

- [Zawinski's Law - Wikipedia](https://en.wikipedia.org/wiki/Jamie_Zawinski#Zawinski%27s_Law) — Wikipedia section on Zawinski's Law
- [Don't Let Architecture Astronauts Scare You](https://www.joelonsoftware.com/2001/04/21/dont-let-architecture-astronauts-scare-you/) — Joel Spolsky's classic essay on software bloat and platformization

### Related Laws

- [Second-System Effect](#second-system-effect)
- [YAGNI (You Aren't Gonna Need It)](design.md#yagni)

---
