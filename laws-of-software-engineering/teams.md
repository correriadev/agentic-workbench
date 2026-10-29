# Laws of Software Engineering — Teams

Extracted from [Laws of Software Engineering](https://lawsofsoftwareengineering.com/). This document covers all **9** principles categorized under **Teams**.

## Table of Contents

- [Conway's Law](#conways-law) — *Organizations design systems that mirror their own communication structure.* (Senior)
- [Brooks's Law](#brooks-law) — *Adding manpower to a late software project makes it later.* (Mid)
- [Dunbar's Number](#dunbars-number) — *There is a cognitive limit of about 150 stable relationships one person can maintain.* (Senior)
- [The Ringelmann Effect](#ringelmann-effect) — *Individual productivity decreases as group size increases.* (Mid)
- [Price's Law](#prices-law) — *The square root of the total number of participants does 50% of the work.* (Senior)
- [Putt's Law](#putts-law) — *Those who understand technology don't manage it, and those who manage it don't understand it.* (Senior)
- [Peter Principle](#peter-principle) — *In a hierarchy, every employee tends to rise to their level of incompetence.* (Mid)
- [Bus Factor](#bus-factor) — *The minimum number of team members whose loss would put the project in serious trouble.* (Mid)
- [Dilbert Principle](#dilbert-principle) — *Companies tend to promote incompetent employees to management to limit the damage they can do.* (Senior)

---

<a id="conways-law"></a>
## Conway's Law

> **Category:** Teams | **Level:** Senior | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/conways-law/](https://lawsofsoftwareengineering.com/laws/conways-law/)

**Organizations design systems that mirror their own communication structure.**

### Key Takeaways

- The architecture of software systems often mirrors the organization’s org chart or team structure.
- If your company is organized in silos, you might end up with siloed software modules that don’t communicate well, reflecting those barriers.
- To achieve a desired software architecture (e.g., microservices), you might need to restructure teams accordingly, because teams build software aligned with their communication paths.
- When starting a project, realize that how you split teams or departments will likely lead to software boundaries at the same places.

### Overview

Conway’s Law states that **software systems reflect the communication structure of the organization that builds them**. A company with separate frontend, backend, and database departments will likely produce a three-tier architecture. Small, distributed teams tend to produce modular service architectures, while large, collocated teams tend to build monoliths.

To mitigate this, teams can use the **Inverse Conway Maneuver**: intentionally structuring the organization to match the desired software architecture.

### Examples

A company had separate departments for frontend, backend, and database. The software they built had a three-tier architecture, with each tier independently designed by its respective department. Integration between tiers was painful because the teams had misaligned goals.

Amazon famously organized “two-pizza teams”, each owning a specific service. Conway’s Law suggests that’s why Amazon’s architecture is service-oriented, with clear API contracts between services.

### Origins

**Melvin Conway** introduced the idea in his 1967 paper “How Do Committees Invent?” After Harvard Business Review rejected it for lacking formal proof, Datamation published it in 1968.

Fred Brooks later named it “Conway’s Law” in *The Mythical Man-Month*, which established the concept as foundational in software engineering.

### Further Reading

- [How Do Committees Invent?](https://www.melconway.com/Home/Committees_Paper.html) — Melvin Conway's original 1968 paper
- [Conway's Law](https://martinfowler.com/bliki/ConwaysLaw.html) — Martin Fowler's explanation of Conway's Law
- [Spotify Engineering Culture](https://engineering.atspotify.com/2014/3/spotify-engineering-culture-part-1) — The original Spotify Model blog post
- [Team Topologies](https://amzn.to/4jgRZ6V) — Modern application of Conway's Law to organizational design

### Related Laws

- [Brooks's Law](#brooks-law)
- [Gall's Law](architecture.md#galls-law)
- [The Law of Leaky Abstractions](architecture.md#law-of-leaky-abstractions)
- [Hyrum's Law](architecture.md#hyrums-law)

---

<a id="brooks-law"></a>
## Brooks's Law

> **Category:** Teams | **Level:** Mid | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/brooks-law/](https://lawsofsoftwareengineering.com/laws/brooks-law/)

**Adding manpower to a late software project makes it later.**

### Key Takeaways

- Simply throwing more developers at a project that’s running behind schedule usually slows it down further initially.
- New people take time to get up to speed, consuming existing team members’ time for training and coordination, which reduces overall productivity.
- Instead of hoping manpower will solve slippage, adjust the scope or timeline. Be wary of ‘just hire more coders’ as a solution to lateness.

### Overview

Brooks’s Law challenges the belief that a software development effort is perfectly divisible among people. In reality, adding a person to a project incurs training costs and increases the number of communication paths. This can outweigh that person’s contribution for a while.

If a project is already late, adding new developers can cause further delays as they learn the system and may introduce new bugs. Brooks illustrated this with the observation that “the bearing of a child takes nine months, no matter how many women are assigned.” The law doesn’t say adding people never helps, but as a response to lateness, it’s usually counterproductive.

### Examples

A project is one month behind schedule, so management adds 3 new developers to a 5-person team. Over the next few weeks, progress slows. The original developers spend much of their time explaining the design and code to newcomers, and merging their work causes integration headaches. The project slips further, now two months late.

A complex bug required deep knowledge of the system. Adding more people didn’t help because only the original dev understood it, and more debuggers only made things worse. Scaling a software team isn’t linear. After a point, more members yield less and less output per person.

### Origins

**Frederick P. Brooks Jr.**, who managed the IBM OS/360 project, formulated this law based on painful experience. His book *The Mythical Man-Month* (1975) explores why software projects fail and where management assumptions break down.

The book famously challenged the notion that “man-months” are interchangeable. Brooks demonstrated through real-world examples why the assumption that 12 programmers can do in one month what one programmer does in 12 months fails in software development.

### Further Reading

- [The Mythical Man-Month](https://amzn.to/4peJbjC) — Fred Brooks's classic book on software engineering
- [Brooks's Law - Wikipedia](https://en.wikipedia.org/wiki/Brooks%27s_law) — Wikipedia article on Brooks's Law
- [No Silver Bullet](https://en.wikipedia.org/wiki/No_Silver_Bullet) — Fred Brooks's essay on essential vs accidental complexity

### Related Laws

- [Conway's Law](#conways-law)
- [Second-System Effect](architecture.md#second-system-effect)
- [Law of Unintended Consequences](architecture.md#law-of-unintended-consequences)

---

<a id="dunbars-number"></a>
## Dunbar's Number

> **Category:** Teams | **Level:** Senior | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/dunbars-number/](https://lawsofsoftwareengineering.com/laws/dunbars-number/)

**There is a cognitive limit of about 150 stable relationships one person can maintain.**

### Key Takeaways

- Dunbar’s number (~150) is the size of a community in which everyone knows each other’s identities and roles. Beyond this, our brains struggle to track relationships.
- In software organizations, teams larger than ~100-150 will require more hierarchy or splitting into subgroups to function effectively. Coordination overhead rises sharply.
- Smaller limits exist for closer relationships. Effective working groups might be much smaller than 150, but 150 is an upper bound for a community feeling.
- Strong collaboration happens in groups far below the 150 threshold. Small teams win.

### Overview

Dunbar’s Number means that an engineering department of 150 might function informally, but as it grows past that, you start needing more formal rules, communication channels, and management layers. Informal knowledge (“I know who to talk to about X”) begins to fail, and teams feel impersonal.

The rule encourages designing sub-teams or “teams of teams” that are small enough to work together effectively. Dunbar also proposed smaller social layers: ~5 intimate relationships, ~15 trusted collaborators, ~50 close working relationships, and ~150 stable social connections.

For software teams, high-trust work happens in tiny groups, teams larger than ~10-15 lose cohesion, and the 150 limit applies to departments or communities, not day-to-day collaboration.

### Examples

Many startups report that around the 150-employee mark, the culture shifts. You no longer know everyone’s name, informal communication falters, and you start needing all-hands meetings and internal newsletters. That’s Dunbar’s number in action.

The **Linux kernel community** has thousands of contributors, but within it are maintainers and subsystem teams that are relatively small. Communication is structured into mailing lists by subsystem, so any given person communicates only with a small number of peers.

Amazon’s “two-pizza teams” (5-10 people) show that even within 150, effective working teams are smaller units.

### Origins

**Robin Dunbar** introduced this number in a 1992 paper and popularized it in his book *Grooming, Gossip, and the Evolution of Language*. He found a correlation between primate neocortex size and social group size, predicting human size at ~150.

Examples such as historical village sizes, military company units, and communal groups often hover around 100-200, lending credence to the figure.

### Further Reading

- [Dunbar's Number - Wikipedia](https://en.wikipedia.org/wiki/Dunbar%27s_number) — Wikipedia article on Dunbar's number
- [Grooming, Gossip, and the Evolution of Language](https://www.amazon.com/Grooming-Gossip-Evolution-Language-Dunbar/dp/0674363361) — Robin Dunbar's book introducing the concept

### Related Laws

- [Conway's Law](#conways-law)
- [Brooks's Law](#brooks-law)

---

<a id="ringelmann-effect"></a>
## The Ringelmann Effect

> **Category:** Teams | **Level:** Mid | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/ringelmann-effect/](https://lawsofsoftwareengineering.com/laws/ringelmann-effect/)

**Individual productivity decreases as group size increases.**

### Key Takeaways

- In large teams, some people put in less effort because they assume others will pick up the slack or because their contributions are less visible.
- More people mean more communication, meetings, and alignment needed. Time spent coordinating increases, leaving less time for actual work.
- There is a point at which adding people yields diminishing returns, or even negative returns per person. Small, focused teams often outperform poorly coordinated larger teams.
- Smaller teams or individuals feel greater ownership and responsibility.

### Overview

The Ringelmann Effect states that as more people work together, individual effort decreases. In software teams, productivity per person often declines in larger groups due to coordination overhead and some individuals contributing less when in a crowd.

This effect warns that adding team members can make each existing member less efficient. Along with Brooks’s Law, it shows that teamwork doesn’t scale linearly. Teams must be structured to mitigate this with clear roles and small, focused groups.

### Examples

In a brainstorming session with 3 people, each might contribute many ideas. In a session with 15 people, many participants will say nothing, assuming others will speak.

If 10 developers work on one module, merging code, resolving conflicts, and communicating design decisions can consume significant time. This effect motivates Amazon’s “Two Pizza Rule” (a team feedable by two pizzas, roughly 5-8 people).

### Origins

Named after **Max Ringelmann**, a French agricultural engineer who observed it in physical tasks around 1913. He found that when people pulled on a rope together, each individual exerted less force than when pulling alone.

The phenomenon was later termed “social loafing” in psychology. It has been demonstrated in many group situations beyond rope pulling, from cognitive tasks to workplace productivity.

### Further Reading

- [Ringelmann Effect - Wikipedia](https://en.wikipedia.org/wiki/Ringelmann_effect) — Wikipedia article on the Ringelmann effect
- [Social Loafing - Wikipedia](https://en.wikipedia.org/wiki/Social_loafing) — The psychological phenomenon behind the effect
- [The Two Pizza Rule](https://aws.amazon.com/executive-insights/content/amazon-two-pizza-team/) — Amazon's approach to keeping teams small and effective
- [The Tipping Point](https://amzn.to/4jfJ1Hb) — Malcolm Gladwell's book exploring how small changes can have big effects
- [From Aristotle to Ringelmann: A Large-Scale Analysis of Team Productivity and Coordination in Open Source Software Projects](https://doi.org/10.1007/s10664-015-9406-4) — Scholtes, Mavrodiev & Schweitzer (2016) - empirical study of team productivity and coordination in OSS projects

### Related Laws

- [Brooks's Law](#brooks-law)
- [Dunbar's Number](#dunbars-number)
- [Conway's Law](#conways-law)

---

<a id="prices-law"></a>
## Price's Law

> **Category:** Teams | **Level:** Senior | **Read Time:** 3 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/prices-law/](https://lawsofsoftwareengineering.com/laws/prices-law/)

**The square root of the total number of participants does 50% of the work.**

### Key Takeaways

- A small fraction of people often contribute a significant fraction of the results. In a 100-person engineering org, about 10 people might produce half of the output.
- As teams grow, productive output doesn’t scale linearly. Adding more people increases total output, but many will make smaller contributions than the core group.
- Knowing this helps in team planning and understanding why losing specific individuals has a significant impact on productivity.
- It’s wise to identify and retain the small group of people who are essential to the company’s output.

### Overview

You probably noticed that most of the major work depends on just a few people in your organization, and that is not false. In software teams, it means a relatively small group of engineers will deliver a disproportionately large part of the value. This is similar to the Pareto principle (80/20 rule) but even more extreme for larger groups.

Price’s Law suggests that simply hiring more developers won’t necessarily scale output as expected. Beyond a point, many may contribute little or be working on peripheral tasks. It’s an argument for focusing on quality when hiring: a single excellent engineer can outperform several average ones. However, we must be careful with this “law” as we don’t want to make other people feel useless, as they may be doing essential tasks that are given less importance.

It highlights a risk: if those top √N contributors leave, you lose a large chunk of productivity, so retention and preventing burnout for them are critical.

### Examples

Take an open-source project on GitHub with 30 contributors. Often, you’ll see that maybe 5 contributors (roughly √30 ≈ 5) are responsible for about half the code commits or major features. The rest contribute smaller patches or documentation.

A notable example is when Twitter cut staff after Musk bought it, yet the product kept running. Before the takeover, Twitter had roughly 7,500 employees, meaning √7,500 ≈ 87. Price’s law suggests that when the new leadership decided to lay off almost 50% of staff, the platform could still operate if the core 80-100 people stayed. But this holds only if the proper people are selected. The law won’t predict reliability, as layoffs strip redundancy in SRE, security, and moderation. Twitter even asked some laid-off workers to return, a signal that it missed critical skills.

### Origins

**Derek de Solla Price**, a British physicist, historian of science, and information scientist, discovered this pattern while studying his peers in academia. He noticed that there were always a handful of people who dominated publications within a subject.

He introduced this concept in his 1963 book “Little Science, Big Science” as part of his broader research on scientific productivity and information dynamics. The law has since been generalized to various fields, though empirical data suggests it’s more of a model than an absolute rule, as the related Lotka’s law often fits better.

### Further Reading

- [Price's Law - Wikipedia](https://en.wikipedia.org/wiki/Price%27s_law) — Wikipedia article on Price's Law and its empirical challenges
- [Derek J. de Solla Price - Wikipedia](https://en.wikipedia.org/wiki/Derek_J._de_Solla_Price) — Biography of the scientist who discovered the law

### Related Laws

- [The Ringelmann Effect](#ringelmann-effect)
- [Brooks's Law](#brooks-law)
- [Dunbar's Number](#dunbars-number)

---

<a id="putts-law"></a>
## Putt's Law

> **Category:** Teams | **Level:** Senior | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/putts-law/](https://lawsofsoftwareengineering.com/laws/putts-law/)

**Those who understand technology don't manage it, and those who manage it don't understand it.**

### Key Takeaways

- There is often a gap between deep technical understanding and management roles. Rarely does one person excel at both.
- Technical experts often aren’t in management, and managers usually don’t understand the technical details.
- This can lead to unrealistic expectations, such as when management sets unrealistic expectations because they don’t understand the domain and its complexity. At the same time, engineers are feeling misunderstood.
- Successful organizations bridge this by training managers in tech basics or promoting technically savvy leaders.

### Overview

Putt’s Law explains a known concept: that the best engineers aren’t in charge, and those in charge aren’t deeply knowledgeable about the technology. While not universally true, this highlights a real challenge: managing technologists requires some understanding of their work. But managers often come from different backgrounds or have been away from the code for a long time.

The law’s corollary states: “Every technical hierarchy, in time, develops a competence inversion,” meaning the people at the top know less about the work than those below. The gap creates dysfunction: managers set unrealistic deadlines because they don’t understand technical subjects, while engineers build wrong solutions because they don’t understand the business context.

The lesson is clear: technical leadership should maintain technical competence or risk mismanaging the technical work.

### Examples

Think of a software manager who came from a sales or business background. They might push the team to add complex features at warp speed, failing to understand why quality or testing is needed. They “manage what they do not understand.”

On the other side, a brilliant sysadmin knows precisely how to optimize infrastructure but isn’t involved in management decisions about budgeting or project direction. They “understand what they do not manage.”

Perhaps the manager promises a client a feature by next week (not understanding the technical difficulty), and the engineering team is frustrated because the manager didn’t realize what’s involved. Many startups initially avoid this because founders often manage and deeply understand the tech, but as companies grow, specialization separates roles. One remedy is to have CTOs or tech leads act as a bridge, with one foot in management and one in technical detail.

### Origins

Putt’s Law was revealed in the satirical book “Putt’s Law and the Successful Technocrat” (1981). The author used the pseudonym “Archibald Putt.”

The book offers a cynical but insightful look at the dynamics of technical organizations and how competence often gets inverted as people rise through hierarchies. It overlaps conceptually with the Peter Principle (people rise to their level of incompetence) and the Dilbert Principle (incompetent people end up in management).

### Further Reading

- [Putt's Law and the Successful Technocrat - Amazon](https://amzn.to/4aAuOm0) — The original satirical book by Archibald Putt
- [The Boeing 737 MAX: Lessons for Engineering Ethics](https://doi.org/10.1007/s11948-020-00252-y) — Herkert, Borenstein & Miller (2020) - examines how management decisions overriding technical expertise led to disaster

### Related Laws

- [Peter Principle](#peter-principle)
- [Dilbert Principle](#dilbert-principle)

---

<a id="peter-principle"></a>
## Peter Principle

> **Category:** Teams | **Level:** Mid | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/peter-principle/](https://lawsofsoftwareengineering.com/laws/peter-principle/)

**In a hierarchy, every employee tends to rise to their level of incompetence.**

### Key Takeaways

- People get promoted based on success in their current role until they reach a position where they are no longer competent.
- A great developer promoted to manager might perform poorly, losing a good developer and gaining a bad manager.
- Organizations should offer dual career paths (technical vs. managerial) to prevent this stagnation.

### Overview

The Peter Principle explains why organizations often end up with mediocre managers. A great engineer gets promoted to tech lead but struggles in the role, and now the company has lost a great engineer.

For a healthy organization, it’s essential to mitigate this. Not every senior engineer should become a manager; some might advance as staff or principal engineers instead. New managers need training to be competent in their new role.

The Peter Principle warns that promotion systems can create mediocrity at higher levels if not designed carefully.

### Examples

In a development team, Alice is the best programmer. Management appoints her team manager since she’s the most experienced. But she has no experience or desire for people management. As a result, the team struggles. She either micromanages or misses essential management tasks, all while coding less (her main strength). Alice has reached her “level of incompetence” and might remain in that role indefinitely.

Consider a QA engineer fantastic at finding bugs who gets promoted to QA Lead, a role involving paperwork and strategy. If those aren’t their strengths, the QA process might decline.

Many tech organizations now use **individual contributor (IC) career tracks** to combat this, allowing great engineers to remain engineers with raises and titles rather than forcing them into management to advance. The principle also encourages rotations or acting in leadership roles to ensure competence before permanent assignments.

### Origins

The Peter Principle was described in the book “The Peter Principle” by **Laurence J. Peter** in 1969. It was meant as a humorous piece of sociology and business insight.

Scott Adams’ Dilbert Principle later riffed on it, cynically inverting the idea by suggesting companies promote incompetent people to get them out of the workflow. Both highlight absurdities in corporate culture.

### Further Reading

- [The Peter Principle - Wikipedia](https://en.wikipedia.org/wiki/Peter_principle) — Overview of the Peter Principle and its implications
- [The Peter Principle: Why Things Always Go Wrong - Amazon](https://amzn.to/48XHHW7) — The original 1969 book by Laurence J. Peter

### Related Laws

- [Dilbert Principle](#dilbert-principle)
- [Putt's Law](#putts-law)

---

<a id="bus-factor"></a>
## Bus Factor

> **Category:** Teams | **Level:** Mid | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/bus-factor/](https://lawsofsoftwareengineering.com/laws/bus-factor/)

**The minimum number of team members whose loss would put the project in serious trouble.**

### Key Takeaways

- A bus factor of 1 means one person holds critical knowledge; if they disappear, the project is essentially ‘doomed’ or stalled. A higher bus factor (e.g., 5) means the project could lose any one of five specific people before stopping work.
- It’s basically a measure of knowledge distribution and risk. A high bus factor is good (knowledge is shared among many), while a low is bad (single points of failure in expertise).
- Teams should work to increase their bus factor by sharing knowledge, documenting critical systems, having code reviews, and rotating responsibilities.

### Overview

The Bus Factor highlights the human single point of failure in projects. In many software teams, one or two people might understand the legacy system, a crucial algorithm, or have all the deployment knowledge. If those people leave, others cannot easily pick up the work.

The concept encourages actively avoiding such dependency. Improving bus factor overlaps with knowledge management practices: pair programming, code reviews, documentation, mentorship, and rotating responsibilities.

### Examples

If a startup’s only database expert is Alice, the bus factor for database knowledge is 1. If Alice quits, nobody else knows the backups, schema intricacies, or tuning.

The **Left-pad incident** reflects a bus factor of 1 for the broader ecosystem: a single maintainer pulled a tiny NPM package, and thousands of builds broke.

### Origins

The concept was popularized in the 1990s in discussions of project risk. The term is somewhat morbid, so some call it “lottery factor” (flipping the scenario to a positive reason someone leaves).

It’s not attributed to a single person but emerged as slang in software teams. An early reference appears in patterns literature (1994 PLoP conference), discussing “truck number” in organizational patterns. The idea likely existed informally even earlier.

### Further Reading

- [Bus Factor - Wikipedia](https://en.wikipedia.org/wiki/Bus_factor) — Overview of the Bus Factor concept and its implications
- [Left-pad incident - Wikipedia](https://en.wikipedia.org/wiki/Npm_left-pad_incident) — A real-world example of bus factor risk in open source
- [The Dead Sea Effect - Bruce F. Webster](https://brucefwebster.com/2008/04/11/the-wetware-crisis-the-dead-sea-effect/) — The original article describing how talent drains from dysfunctional organizations
- [If Guido was hit by a bus?](https://legacy.python.org/search/hypermail/python-1994q2/1040.html) — Michael McLay's 1994 mailing list post, one of the earliest references to the bus factor concept
- [Organizational Patterns of Agile Software Development](https://www.wiley.com/en-us/Organizational+Patterns+of+Agile+Software+Development-p-9780131467408) — Coplien & Harrison (2004) - patterns for building effective software organizations

### Related Laws

- [Conway's Law](#conways-law)
- [Brooks's Law](#brooks-law)
- [Dunbar's Number](#dunbars-number)

---

<a id="dilbert-principle"></a>
## Dilbert Principle

> **Category:** Teams | **Level:** Senior | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/dilbert-principle/](https://lawsofsoftwareengineering.com/laws/dilbert-principle/)

**Companies tend to promote incompetent employees to management to limit the damage they can do.**

### Key Takeaways

- Organizations sometimes deal with underperformers by promoting them into management, removing them from hands-on work.
- It reflects a cynical view that lower-level employees do real work while some managers add little value.
- Technical excellence and people leadership require different skills. Failing at one does not qualify someone for the other.

### Overview

The Dilbert Principle suggests that instead of addressing poor performance directly, companies often promote struggling employees into management roles where their impact is perceived as less immediately harmful. The satire resonates because it reflects a fundamental flaw: many organizations treat management as the default career path for engineers without considering what those employees actually want or are suited for.

When promotion replaces accountability, management layers fill with people lacking either technical credibility or leadership ability. The result is bad decisions, wrong priorities, and loss of trust between engineers and leadership.

### Examples

Many engineers share anecdotes that feel straight out of Dilbert. A mediocre programmer or failing project lead gets “promoted” to a management or architect role. Sometimes these moves are less about recognizing leadership talent and more about getting a problematic person away from critical work. The result is counterproductive: you now have an incompetent manager and one fewer developer.

On a positive note, awareness of the Dilbert Principle has made some organizations more careful. Modern tech companies increasingly offer **dual career tracks** (technical vs. managerial) to avoid forcing great engineers into management.

When an underperforming employee can’t succeed in engineering, good companies try coaching or reassignment, and if all else fails, let them go rather than make them the boss.

### Further Reading

- [The Dilbert Principle - Wikipedia](https://en.wikipedia.org/wiki/Dilbert_principle) — Overview of Scott Adams' satirical management theory
- [The Dilbert Principle - Amazon](https://amzn.to/4jgz6kJ) — The original 1996 book by Scott Adams
- [A Cubicle's-Eye View of Bosses, Meetings, Management Fads and Other Workplace Afflictions](https://www.amazon.com/Dilbert-Principle-Cubicles-Eye-Meetings-Management/dp/0887308589) — Scott Adams (1996) - the satirical take on corporate dysfunction that popularized the principle

### Related Laws

- [Peter Principle](#peter-principle)
- [Putt's Law](#putts-law)
- [Brooks's Law](#brooks-law)

---
