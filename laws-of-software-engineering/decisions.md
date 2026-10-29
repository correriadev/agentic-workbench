# Laws of Software Engineering — Decisions

Extracted from [Laws of Software Engineering](https://lawsofsoftwareengineering.com/). This document covers all **12** principles categorized under **Decisions**.

## Table of Contents

- [Dunning-Kruger Effect](#dunning-kruger-effect) — *The less you know about something, the more confident you tend to be.* (Junior)
- [Hanlon's Razor](#hanlons-razor) — *Never attribute to malice that which is adequately explained by stupidity or carelessness.* (Junior)
- [Occam's Razor](#occams-razor) — *The simplest explanation is often the most accurate one.* (Junior)
- [Sunk Cost Fallacy](#sunk-cost-fallacy) — *Sticking with a choice because you've invested time or energy in it, even when walking away helps you.* (Mid)
- [The Map Is Not the Territory](#map-is-not-the-territory) — *Our representations of reality are not the same as reality itself.* (Mid)
- [Confirmation Bias](#confirmation-bias) — *A tendency to favor information that supports our existing beliefs or ideas.* (Mid)
- [The Hype Cycle & Amara's Law](#hype-cycle-amaras-law) — *We tend to overestimate the effect of a technology in the short run and underestimate the impact in the long run.* (Mid)
- [The Lindy Effect](#lindy-effect) — *The longer something has been in use, the more likely it is to continue being used.* (Mid)
- [First Principles Thinking](#first-principles-thinking) — *Breaking a complex problem into its most basic blocks and then building up from there.* (Mid)
- [Inversion](#inversion) — *Solving a problem by considering the opposite outcome and working backward from it.* (Mid)
- [Pareto Principle (80/20 Rule)](#pareto-principle) — *80% of the problems result from 20% of the causes.* (Junior)
- [Cunningham's Law](#cunninghams-law) — *The best way to get the correct answer on the Internet is not to ask a question, it's to post the wrong answer.* (Junior)

---

<a id="dunning-kruger-effect"></a>
## Dunning-Kruger Effect

> **Category:** Decisions | **Level:** Junior | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/dunning-kruger-effect/](https://lawsofsoftwareengineering.com/laws/dunning-kruger-effect/)

**The less you know about something, the more confident you tend to be.**

### Key Takeaways

- Confidence without context is unreliable. Early confidence often signals ignorance, not mastery.
- Awareness grows faster than skill. Learning initially reduces confidence, only to rebuild it.
- Real experts speak in ranges, trade-offs, and probabilities, not with confidence about every topic.

### Overview

The Dunning-Kruger Effect explains a gap between confidence and competence. When people know little about a domain, they lack the awareness required to judge their own ability. As a result, they overestimate how well they understand the problem.

As learning progresses, people discover the depth and complexity of the domain.

Awareness of unknowns grows faster than capability, leading to a drop in confidence, often called the “valley of despair.” Only after experience does confidence rise again, now with fundamental understanding.

### Examples

New developers often give confident, precise estimates, while experienced developers give ranges (the famous “it depends” answer). The juniors aren’t being careless; they simply don’t yet know what they don’t know (unknown-unknowns).

Peak enthusiasm for a new technology often comes from those who have used it least. Those with deep experience are more measured.

We should also note that *Impostor syndrome* reflects miscalibration in the opposite direction. Skilled individuals underestimate their competence because they are deeply aware of complexity and edge cases.

### Origins

The effect was described by psychologists **David Dunning** and **Justin Kruger** in a 1999 study at Cornell University. Their experiments showed that people with low performance consistently overestimated their ability on logic, grammar, and humor tests, while high performers underestimated their ability.

The proposed mechanism is simple: the skills required to perform well are often the same skills needed to assess performance accurately.

One caveat: the original study measured how people rank themselves against peers. Low performers overestimated their relative standing, but they were not more confident than experts; the popular “peak of confidence” curve is a later simplification of the findings.

### Further Reading

- [Dunning-Kruger Effect - Wikipedia](https://en.wikipedia.org/wiki/Dunning%E2%80%93Kruger_effect) — Comprehensive overview of the cognitive bias and its research
- [Unskilled and Unaware of It - Original 1999 Paper](https://psycnet.apa.org/doi/10.1037/0022-3514.77.6.1121) — The original study by Kruger and Dunning in the Journal of Personality and Social Psychology
- [We Are All Confident Idiots - David Dunning](https://psmag.com/social-justice/confident-idiots-92793) — David Dunning's accessible article in Pacific Standard explaining the effect
- [Thinking, Fast and Slow](https://amzn.to/48WboH0) — Daniel Kahneman's seminal book on cognitive biases and decision-making

### Related Laws

- [Brooks's Law](teams.md#brooks-law)
- [Hanlon's Razor](#hanlons-razor)

---

<a id="hanlons-razor"></a>
## Hanlon's Razor

> **Category:** Decisions | **Level:** Junior | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/hanlons-razor/](https://lawsofsoftwareengineering.com/laws/hanlons-razor/)

**Never attribute to malice that which is adequately explained by stupidity or carelessness.**

### Key Takeaways

- When something goes wrong, it’s likely not malicious but rather an error or misunderstanding.
- Don’t jump to ’the system is hacked’ or ‘someone intentionally broke this.’ First, consider simpler explanations (e.g., a configuration file was missed or a typographical error).
- If a colleague’s code is problematic, it’s probably not sabotage. It may be due to being rushed or unaware of something. Try to approach with questions, not accusations.

### Overview

Hanlon’s Razor advises against assuming bad faith when an outcome may be due to human error or ignorance. If a commit introduces a security hole, it’s probably a mistake, not intentional sabotage. So one responds with help and fixes, not with blame.

This doesn’t mean ignoring the possibility of malice when truly warranted (security does consider malicious actors). But for day-to-day development and operations, Hanlon’s Razor keeps you grounded: the build failed likely due to a misconfiguration, not because someone deliberately broke it.

### Examples

A customer reports that your software “deleted all my data!” It’s easy to panic and think a disgruntled employee planted a logic bomb. But Hanlon’s Razor would have you first check for a mundane bug, perhaps a boundary condition in a delete function that wipes more than intended. Indeed, you find a bug where, when a user’s account name was empty, the cleanup script deleted all records. No malice, just a bug.

In security, consider a sudden spike in server traffic. Before screaming “it’s a DDoS attack!”, check first if it’s a misconfigured client spamming or a known pattern. Most weird behaviors in systems are due to mistakes, not malicious intent.

### Further Reading

- [Hanlon's Razor - Wikipedia](https://en.wikipedia.org/wiki/Hanlon%27s_razor) — Overview of the principle and its origins
- [Blameless Postmortems - Etsy](https://www.etsy.com/codeascraft/blameless-postmortems/) — How Etsy applies blameless culture in incident response
- [The Field Guide to Understanding Human Error](https://amzn.to/3LbyIas) — Sidney Dekker's book on human factors in system failures

### Related Laws

- [Occam's Razor](#occams-razor)
- [Goodhart's Law](planning.md#goodharts-law)
- [Postel's Law](quality.md#postels-law)

---

<a id="occams-razor"></a>
## Occam's Razor

> **Category:** Decisions | **Level:** Junior | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/occams-razor/](https://lawsofsoftwareengineering.com/laws/occams-razor/)

**The simplest explanation is often the most accurate one.**

### Key Takeaways

- Simple code is easier to understand, maintain, and debug, whereas complex code has more potential points of failure. Remove or avoid unnecessary moving parts in system architecture.
- When debugging, start with the simplest explanation before jumping into complex theories.
- Adding more features to the app can only complicate a product without adding real value. Occam’s Razor reminds us that less is more in many cases.

### Overview

Occam’s Razor is a problem-solving principle that reminds us that when we have multiple possible solutions, the simplest one is preferred.

In software, this principle supports the KISS (“Keep It Simple, Stupid”) approach. When we decide to keep our implementations simple, we reduce the risk of further complications.

For example, if a software architecture can achieve its goals with a monolith and one database, there is no need to split it into five microservices and two databases. These extra components would only introduce complexity and potential integration and coordination issues, but no benefits.

This is a reminder to avoid the temptation of over-engineering and keep things simple.

### Examples

A classic example of applying Occam’s Razor while debugging is that of the broken build. Let’s assume that your build system has failed. A complex thinker might think that there is some subtle regression in the compiler code, or maybe some dependency is damaged. An Occam’s Razor thinker would start with simpler explanations: a typo, a missing semicolon, or a misconfiguration.

A saying often attributed to Einstein goes, “Everything should be made as simple as possible, but not simpler,” which best applies to this law in engineering.

### Origins

Occam’s Razor dates back to William of Ockham, a philosopher from 14th-century England. His original version in Latin, “Pluralitas non est ponenda sine necessitate,” can be translated to “plurality should not be posited without necessity,” or “Don’t multiply entities or assumptions beyond what’s required.”

Over time, Occam’s Razor has evolved as a cornerstone of scientific methodology and logical reasoning.

### Further Reading

- [Ockham's Razors: A User's Manual](https://amzn.to/4jfnRZX) — Elliott Sober's comprehensive analysis of parsimony in science
- [Inference to the Best Explanation](https://www.routledge.com/Inference-to-the-Best-Explanation/Lipton/p/book/9780415242028) — Peter Lipton's exploration of explanatory reasoning and simplicity
- [Simplicity (Stanford Encyclopedia of Philosophy)](https://plato.stanford.edu/entries/simplicity/) — In-depth philosophical analysis of Occam's Razor and parsimony principles
- [No Silver Bullet](https://en.wikipedia.org/wiki/No_Silver_Bullet) — Fred Brooks on accidental vs essential complexity in software

### Related Laws

- [KISS (Keep It Simple, Stupid)](design.md#kiss-principle)
- [YAGNI (You Aren't Gonna Need It)](design.md#yagni)
- [Gall's Law](architecture.md#galls-law)

---

<a id="sunk-cost-fallacy"></a>
## Sunk Cost Fallacy

> **Category:** Decisions | **Level:** Mid | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/sunk-cost-fallacy/](https://lawsofsoftwareengineering.com/laws/sunk-cost-fallacy/)

**Sticking with a choice because you've invested time or energy in it, even when walking away helps you.**

### Key Takeaways

- Don’t stay stuck based on past investments. The fact that ‘we’ve invested a year already’ is not an excuse to continue if it’s clearly not working.
- Healthy engineering organizations pivot or stop projects that no longer make sense. Continuing a bad project just because of sunk costs usually leads to greater loss.
- Use clear measures and decision points: ‘If we don’t meet target X by end of quarter, we’ll re-evaluate or discontinue.’
- Teams should feel safe admitting a project isn’t working without fear of blame.

### Overview

The sunk cost fallacy is a cognitive bias that challenges our decision-making. Humans irrationally value what they’ve already invested, whether money, time, or effort, even when those investments can’t be recovered.

In software development, teams often continue working on a feature or product without making progress simply because “we have come this far.”

Understanding this fallacy allows engineers and managers to make more rational choices: past costs should be ignored when deciding the future. Instead, consider current facts and future benefits.

If a rewrite or switch to a third-party solution will clearly save time and money from this point forward, do that, regardless of how much was sunk into the old approach.

Overcoming sunk-cost bias is tough because it requires admitting past efforts were in vain, but in technology it’s crucial to learn to let go when evidence demands.

### Examples

Consider a company that spent two years building a custom in-house CMS, only to find it’s buggy and team productivity is low. An objective analysis might show it’s better to adopt an off-the-shelf CMS. Yet the engineering leadership hesitates: “We invested two years in this; abandoning it means that time was wasted!” If they persist solely for that reason, they fall for the sunk cost fallacy.

A positive example is Google, known for periodically killing off underperforming products (the [Google Graveyard](https://killedbygoogle.com/)). This practice means companies don’t need to move forward with bad decisions once it’s clear an initiative isn’t working.

Teams that conduct pre-mortems or use agile sprints to reassess work frequently are better at avoiding sunk-cost traps.

### Origins

The concept of sunk costs comes from economics. The term “sunk cost fallacy” was popularized by behavioral economists and psychologists in the late 20th century. Nobel laureates Daniel Kahneman and Amos Tversky studied this and related decision biases in the 1970s.

Behavioral economist Richard Thaler officially coined the term “sunk cost fallacy” around 1980.

### Further Reading

- [The Psychology of Sunk Cost](https://www.sciencedirect.com/science/article/abs/pii/0749597885900494) — Arkes & Blumer's 1985 foundational paper on sunk cost psychology
- [The Sunk Cost Fallacy](https://thedecisionlab.com/biases/the-sunk-cost-fallacy) — Comprehensive overview with examples from behavioral science perspective
- [Thinking, Fast and Slow](https://amzn.to/4sfXfMr) — Daniel Kahneman's seminal book covering cognitive biases including sunk costs

### Related Laws

- [Occam's Razor](#occams-razor)
- [Technical Debt](quality.md#technical-debt)
- [Second-System Effect](architecture.md#second-system-effect)

---

<a id="map-is-not-the-territory"></a>
## The Map Is Not the Territory

> **Category:** Decisions | **Level:** Mid | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/map-is-not-the-territory/](https://lawsofsoftwareengineering.com/laws/map-is-not-the-territory/)

**Our representations of reality are not the same as reality itself.**

### Key Takeaways

- Design docs, UML diagrams, and architecture schematics are abstractions. Don’t confuse the blueprint with the actual running software.
- When implementing a system, expect that unforeseen factors will emerge that weren’t captured in the initial designs. Be prepared to adapt the plan as you discover new ’terrain’ during development and testing.
- Models and designs are valuable for guiding development, but always be willing to question assumptions when evidence from the real system contradicts them.

### Overview

“The Map Is Not the Territory” is a mental model originating from general semantics. It encapsulates the idea that our perceptions or conceptual models of things are not the things themselves.

In software, we constantly create “maps”: requirements documents map user needs, architecture diagrams map how components should interact, and our mental understanding of a codebase is a personal map of how we think the code works.

These maps are useful and necessary. Without them, we couldn’t plan or reason about complex systems. However, problems arise when we forget the map’s limits.

A typical example is overconfidence in initial design: a team designs a system on paper, but when coding begins, they discover modules cannot communicate due to latency issues not captured in their assumptions.

As statistician George Box said, “All models are wrong, but some are useful.”

### Examples

Consider designing a microservice system where Service A communicates with Services B and C via Kafka topics. The diagram assumed “the network is reliable” or “latency is negligible,” but in cloud infrastructure reality, those assumptions fall apart. The team updates the design to include retry mechanisms or schema validation.

In performance modeling, an engineer might model a database handling 10,000 queries per second based on specs. In production, due to specific query patterns and data distribution, it only achieves 5,000 qps. The model didn’t account for query plan edge cases.

The Agile methodology itself embodies “map vs territory” thinking: instead of detailed 2-year plans, Agile uses short iterations with continuous feedback from reality to correct its maps.

### Further Reading

- [Science and Sanity](https://www.holybooks.com/wp-content/uploads/Science-and-Sanity.pdf) — Alfred Korzybski's foundational work on general semantics
- [Steps to an Ecology of Mind](https://www.press.uchicago.edu/ucp/books/book/chicago/S/bo3620295.html) — Gregory Bateson's collected essays on anthropology, psychiatry, and epistemology

### Related Laws

- [Goodhart's Law](planning.md#goodharts-law)
- [Gall's Law](architecture.md#galls-law)
- [The Law of Leaky Abstractions](architecture.md#law-of-leaky-abstractions)

---

<a id="confirmation-bias"></a>
## Confirmation Bias

> **Category:** Decisions | **Level:** Mid | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/confirmation-bias/](https://lawsofsoftwareengineering.com/laws/confirmation-bias/)

**A tendency to favor information that supports our existing beliefs or ideas.**

### Key Takeaways

- When reviewing code or debugging, notice if you’re only looking for evidence that supports your initial hunch.
- Challenge yourself when actively thinking about problems. If you have an opinion about an issue, try to ask, ‘What would I expect to see if I’m wrong?’ In this, we can counteract our natural bias only to confirm.
- Regarding team decision-making (for example, tech stacks and/or design decisions), seek input from people with differing opinions. Bias confirmation can be overcome by looking into alternative solutions. For example, if the whole team ‘feels’ that technology X is the superior choice, assign someone to look into the opposing view on technology X.
- Base decision-making on objective criteria (facts, not opinions). Automated tests, performance criteria, and experimentation (A/B tests) can provide truths regardless of human bias.

### Overview

We all like to be right. Confirmation bias is our mind’s way of cheating to feel right more often. Psychologically, once we form an opinion, we subconsciously filter information, noticing bits that support our view and ignoring those that contradict it.

In software, a typical scenario is debugging. A developer convinced that module A caused a production issue will comb through module A’s code intensively. If module B (assumed to be fine) is also throwing errors, they might not even look there, missing the real cause. Awareness of this bias leads to asking “What am I missing? Maybe there is another explanation?” and encouraging environments where beliefs are constructively questioned.

### Examples

In code reviews, a reviewer who trusts a colleague’s skills might skim over potential issues, assuming the code is probably fine. Or the opposite: a reviewer expecting sloppy code from a junior developer might find “issues” that aren’t really important.

Confirmation bias also affects testing. A developer may write unit tests that assert the code works on typical inputs (happy path), but might not try edge cases that could break it. Teams combat this through code reviews with fresh eyes, writing tests specifically aimed at breaking their own code, and post-mortems asking “What went wrong and why didn’t we see it?”

By checking for confirmation bias, engineers can become better at solving problems with an open and critical mind.

### Origins

One of the first to identify confirmation bias was Peter Cathcart Wason, an English cognitive psychologist. In 1960, he conducted a famous experiment (Wason’s rule discovery task) where participants had to guess a rule for a sequence of numbers. He found people tended to test sequences that would confirm their initial thoughts rather than those that could prove them wrong.

Wason coined the term “confirmation bias” to explain this phenomenon. Since then, countless studies have confirmed the existence of confirmation bias in human reasoning.

### Further Reading

- [Confirmation Bias: A Ubiquitous Phenomenon in Many Guises](https://journals.sagepub.com/doi/10.1037/1089-2680.2.2.175) — Raymond Nickerson's comprehensive 1998 review of confirmation bias research
- [On the Failure to Eliminate Hypotheses in a Conceptual Task](https://www.tandfonline.com/doi/abs/10.1080/17470216008416717) — Peter Wason's 1960 foundational paper on the rule discovery task
- [Thinking, Fast and Slow](https://amzn.to/48WboH0) — Daniel Kahneman's exploration of cognitive biases including confirmation bias

### Related Laws

- [Dunning-Kruger Effect](#dunning-kruger-effect)
- [Hanlon's Razor](#hanlons-razor)
- [Goodhart's Law](planning.md#goodharts-law)

---

<a id="hype-cycle-amaras-law"></a>
## The Hype Cycle & Amara's Law

> **Category:** Decisions | **Level:** Mid | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/hype-cycle-amaras-law/](https://lawsofsoftwareengineering.com/laws/hype-cycle-amaras-law/)

**We tend to overestimate the effect of a technology in the short run and underestimate the impact in the long run.**

### Key Takeaways

- Early on, people overestimate what tech can do in the near term, leading to unrealistic expectations.
- In the longer run, the same technology’s true potential emerges, often greater than initially imagined. Amara’s Law reminds us that we tend to underestimate the long-term impact of a significant innovation.
- For developers and tech leaders, this means not getting swept up in the hype cycle. Be patient and evaluate new tools by their proven value, not just the buzz.
- Treat innovation as a limited budget. Good teams use stable, proven tech for most needs and adopt a hyped new technology only when it truly addresses a real problem.

### Overview

This law describes the familiar boom-and-bust hype cycle in tech. Gartner’s Hype Cycle captures the pattern: a new technology triggers inflated expectations, hits a trough of disillusionment when reality falls short, then gradually climbs a slope of enlightenment toward productive mainstream adoption.

In software engineering, many buzzword technologies are initially promoted as game-changers but decline when they cannot deliver promised results. However, after that reality check, some quietly mature and find real usability. The lesson is to have healthy skepticism during hype, but keep an open mind for long-term adoption.

### Examples

AI saw its first big hype wave in the 1960s-70s, when people assumed general AI was just around the corner. When grand promises didn’t materialize, an “AI winter” set in and many abandoned AI as theoretical. But over decades, steady progress continued, and today AI techniques are transforming industries from healthcare to generative AI in software.

Microservices architecture was hyped as the cure for all scaling issues. Many teams hit the trough of disillusionment when they encountered complexity of managing hundreds of services. Now, a more balanced use of microservices is emerging, delivering benefits in the right situations.

### Origins

Amara’s Law is named after Roy Amara, an American researcher and futurist who was president of the Institute for the Future. Amara was an American scientist who began his career as a Navy electronics technician during World War II.

In 1995, the Gartner Hype Cycle framework was introduced by Gartner analyst Jackie Fenn, who noticed a recurring pattern in the maturity of emerging technologies and created a visual graph to describe it.

### Further Reading

- [Gartner Hype Cycle](https://www.gartner.com/en/research/methodologies/gartner-hype-cycle) — Gartner's official explanation of the Hype Cycle methodology
- [Institute for the Future](https://www.iftf.org/) — The organization Roy Amara led, focused on futures thinking and foresight

### Related Laws

- [Goodhart's Law](planning.md#goodharts-law)
- [Gall's Law](architecture.md#galls-law)
- [Second-System Effect](architecture.md#second-system-effect)

---

<a id="lindy-effect"></a>
## The Lindy Effect

> **Category:** Decisions | **Level:** Mid | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/lindy-effect/](https://lawsofsoftwareengineering.com/laws/lindy-effect/)

**The longer something has been in use, the more likely it is to continue being used.**

### Key Takeaways

- The Lindy Effect states that if something (a technology, tool, concept) has persisted for a long time, it will likely continue for much longer.
- For developers, Lindy’s law is a reminder to invest in timeless skills and proven fundamentals (algorithms, core languages, design principles) rather than chasing every new framework that might be obsolete in a few years.
- Use the Lindy Effect when evaluating technology. Things that have been around for some time stick around longer in the future (i.e., choose boring technology).

### Overview

The Lindy Effect turns our intuition about aging on its head. For living creatures, older means less life expectancy. But in technology, it’s often the opposite: the longer something has been in use, the more likely it is to continue being used.

Time acts as a filter. Anything irrelevant, flawed, or fragile tends to disappear, while what remains after many years is usually high-quality and valuable.

This principle serves as a reality check against shiny object syndrome. The majority of so-called “innovations” have little to no relevance to contemporary ideas; rather, they reinvent ideas of the past. Truly fundamental ideas in software (algorithms, data structures, protocols, paradigms) change slowly.

Applying Lindy’s law means favoring things that have “stood the test of time” and learning languages like Python, Java, or C, as well as algorithms, rather than over-focusing on the hottest new framework.

### Examples

COBOL is a language from 1959, over 60 years old, yet it still runs a large amount of the world’s finance and government infrastructure. Some estimates suggest 70-80% of all global financial transactions rely on COBOL code in banking systems and mainframes.

Many JavaScript frameworks like AngularJS, Ember.js, and Knockout.js emerged and fell out of favor over the past decade. Yet the underlying language and browser APIs have been around for over 25 years and will continue.

If choosing between learning a cutting-edge framework and SQL, the Lindy approach suggests SQL (from the 1970s) is still highly relevant today and will remain so.

### Origins

The term was coined in 1964 by journalist Albert Goldman, named after Lindy’s Delicatessen in New York City, a famous hangout for entertainers. Comedians there observed that a Broadway show’s longevity predicted its future run length: if a show had lasted X weeks, it could be expected to run another X weeks.

Nassim Nicholas Taleb brought it to a broad audience in his books “The Black Swan” (2007) and “Antifragile” (2012), giving it the name “Lindy Effect” to describe the aging of non-perishable things like books, ideas, technologies, or traditions.

### Further Reading

- [Antifragile: Things That Gain from Disorder](https://amzn.to/4bc1Ust) — Nassim Nicholas Taleb's book that popularized the Lindy Effect concept
- [An Expert Called Lindy](https://medium.com/incerto/an-expert-called-lindy-fdb30f146eaf) — Taleb's essay exploring the Lindy Effect in depth

### Related Laws

- [Hyrum's Law](architecture.md#hyrums-law)
- [Postel's Law](quality.md#postels-law)
- [The Hype Cycle & Amara's Law](#hype-cycle-amaras-law)

---

<a id="first-principles-thinking"></a>
## First Principles Thinking

> **Category:** Decisions | **Level:** Mid | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/first-principles-thinking/](https://lawsofsoftwareengineering.com/laws/first-principles-thinking/)

**Breaking a complex problem into its most basic blocks and then building up from there.**

### Key Takeaways

- Do not accept the problem as it is. Break the problem down into its inherent parts and then question your assumptions: Are they really true, or are they just accepted standards? Once you grasp the underlying requirements, you may develop new solutions.
- Just because ’everyone uses Framework Y for this’ isn’t a reason you should do so. First principles thinking pushes you to ask why people do certain things the way they do.
- Rather than saying, ‘This feature will take 3 months because that’s how long similar features took,’ break the feature down. Estimate from the basics, which can sometimes show that the ‘similar’ feature had additional issues that you may not have anymore.

### Overview

First-principles thinking solves problems by questioning existing solutions rather than blindly copying them. Instead of “We’ll do X because that other project did X,” ask: “What are we really trying to accomplish? What are constraints versus assumptions?” This approach is good for incremental improvements but essential for fundamental changes.

In software design, first principles challenge how current systems work: “If we started from scratch today, how would we build this?” This thinking led to microservices (questioning the monolith) and serverless computing (questioning server management). The drawback is that it is mentally intensive and not always necessary. Many problems are well-solved by known patterns.

### Examples

Before SpaceX, launching rockets was costly because industry practice used expensive materials and discarded rockets after one use. Elon Musk applied first-principles thinking: What is a rocket made of? Mainly aluminum, titanium, copper, and carbon fiber. Raw material costs were a fraction of finished rocket prices. From that insight, SpaceX decided to build rockets from scratch and make them reusable.

In software, consider a company paying licensing fees for a proprietary analytics platform. An engineer challenged this by examining what the platform actually does: ingest data, run statistical computations, generate reports. These could be implemented using open-source software and custom programming. A proof-of-concept in Python showed 90% of the solution at a fraction of the cost.

### Origins

The term “first principles” has roots in classical philosophy. Aristotle referred to first principles as foundational propositions that cannot be deduced from anything else, the bedrock of knowledge. René Descartes emphasized starting from fundamental truths (“I think, therefore I am”).

In modern times, first-principles thinking gained fame through Elon Musk, who credits it for SpaceX and Tesla innovations. Instead of thinking “rockets are expensive,” he broke down raw material costs and realized building in-house was viable.

### Further Reading

- [First Principles: The Building Blocks of True Knowledge](https://fs.blog/first-principles/) — Farnam Street's comprehensive guide to first principles thinking
- [Posterior Analytics - Aristotle](https://plato.stanford.edu/entries/aristotle-logic/) — Stanford Encyclopedia of Philosophy on Aristotle's foundational logic
- [How to Solve It - George Pólya](https://amzn.to/4b9q3Qo) — Classic book on mathematical problem-solving and heuristics

### Related Laws

- [Occam's Razor](#occams-razor)
- [KISS (Keep It Simple, Stupid)](design.md#kiss-principle)
- [Gall's Law](architecture.md#galls-law)

---

<a id="inversion"></a>
## Inversion

> **Category:** Decisions | **Level:** Mid | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/inversion/](https://lawsofsoftwareengineering.com/laws/inversion/)

**Solving a problem by considering the opposite outcome and working backward from it.**

### Key Takeaways

- For any goal, also ask the inverted question. If the goal is ‘deliver the project on time,’ we should think about ‘what would make us miss the deadline?’ Making a list of those factors (scope creep, underestimating tasks, etc.) can help us achieve those goals and escape issues.
- Use techniques like pre-mortems. Our project failed, and we tried to determine what could have caused it. This critical thinking can show risks that optimistic planning overlooks.
- In design and testing, we can account for edge cases and use cases of your system. For example, how could a malicious user break this API? Inverting in this way leads to better solutions (e.g., adding validation, rate limiting, etc., once you understand how things break).

### Overview

The core idea is that specific insights become clear when you look at a problem from the opposite angle. In software engineering, instead of designing only for the best case, you deliberately design for the worst case: What if the database goes down? What if latency spikes?

By thinking of how things can fail, you add features like circuit breakers, retries, or failover strategies. Inversion pairs well with First-Principles Thinking and is a form of defensive design that leads to robust outcomes by avoiding possible problems.

### Examples

**Netflix’s Chaos Monkey** is a prime example. Usually, engineers try to keep systems running. Chaos Monkey does the opposite: it randomly terminates servers in production to test resilience. This allowed Netflix to build fault-tolerant services that survive server failures.

**Test-Driven Development (TDD)** applies inversion by writing a failing test first. You define the failure before writing code to make it pass, forcing you to think about how code could fail before implementing it.

### Origins

Inversion is explained by investor Charlie Munger’s famous quote: “All I want to know is where I’m going to die, so I’ll never go there.” Munger was inspired by 19th-century mathematician Carl Gustav Jacobi, who solved problems by inverting them and coined “Invert, always invert.”

In philosophy and Stoic practice, we also see a flavor of inversion. The Stoics had an exercise called premeditatio malorum (premeditation of evils), which means imagining in advance the worst things that could happen, just to be prepared. This is essentially inversion applied to life.

### Further Reading

- [Poor Charlie's Almanack - Charlie Munger](https://www.stripe.press/poor-charlies-almanack) — Collection of Munger's speeches and talks on mental models including inversion
- [Antifragile - Nassim Nicholas Taleb](https://en.wikipedia.org/wiki/Antifragile_%28book%29) — Book exploring systems that gain from disorder and stress

### Related Laws

- [First Principles Thinking](#first-principles-thinking)
- [Murphy's Law / Sod's Law](quality.md#murphys-law)
- [Premature Optimization (Knuth's Optimization Principle)](planning.md#premature-optimization)

---

<a id="pareto-principle"></a>
## Pareto Principle (80/20 Rule)

> **Category:** Decisions | **Level:** Junior | **Read Time:** 3 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/pareto-principle/](https://lawsofsoftwareengineering.com/laws/pareto-principle/)

**80% of the problems result from 20% of the causes.**

### Key Takeaways

- Identify the top 20% of factors that contribute to 80% of whatever you care about. This could be 20% of features that account for 80% of usage, or 20% of bugs that cause 80% of crashes. Prioritize your time and resources on those vital few for maximum impact.
- Don’t spend the same effort on everything. If a particular area of code is rarely run, it probably doesn’t need the same optimization or attention as a hotspot.
- It’s not always exactly 80/20, but the idea is the same. Use profiling, analytics, and data gathering to empirically identify where the imbalances are.
- On a personal level, as an engineer or manager, identify which tasks produce most of your value. It might be coding core features or coaching team members.

### Overview

The Pareto Principle is more of an observation than a law, but the 80/20 pattern (or similar ratios like 90/10) appears frequently.

In the domain of software engineering we say that, “80% of the time in a program is spent in 20% of the code.” This insight is significant for optimization: instead of micro-optimizing everything, profile to identify the hot 20% and optimize that.

The principle influences product development too. Often, a few core features satisfy the majority of user needs. When planning an MVP, teams focus on that core set rather than trying to do everything. It is an essential check against equal prioritization: everything is not equally important.

The Pareto Principle encourages strategic allocation of effort to maximize outcomes by investing where returns are highest.

### Examples

Microsoft found that around **20% of bugs in Windows and Office caused 80% of all crashes**, and a tiny 1% of bugs caused around 50% of errors. By focusing on the critical 1-20% of bugs, they dramatically improved stability. This is textbook Pareto: address the small set of high-impact issues to make most users happier quickly.

A software team analyzed usage analytics and discovered that out of 50 features, only 5-10 (10-20%) were used by 80%+ of users. This guided them to simplify the interface around core features and remove unused ones.

**Hot spots in code** follow the Pareto pattern. A small part of the codebase drives most defects, slowdowns, and “scary to touch” work. Track commits plus incidents to find them, then pay down debt where it compounds: add tests, simplify paths, reduce coupling, tighten interfaces.

### Origins

The principle is named after Vilfredo Pareto, an Italian economist who in 1906 noted that about 80% of Italy’s land was owned by 20% of the population.

In the 1940s, quality management pioneer Joseph M. Juran adopted the idea when analyzing industrial defects, calling it the “vital few and trivial many” rule. Juran observed that by focusing on the vital few quality issues, one could improve quality with less effort than trying to tackle all problems at once.

### Further Reading

- [Microsoft's CEO: 80-20 Rule Applies To Bugs](https://www.crn.com/news/security/18821726/microsofts-ceo-80-20-rule-applies-to-bugs-not-just-features) — How Microsoft applied Pareto to prioritize bug fixes
- [The 80/20 Principle - Richard Koch](https://amzn.to/44QjIFH) — Book on applying the Pareto Principle to business and life
- [Pareto Principle - Wikipedia](https://en.wikipedia.org/wiki/Pareto_principle) — Overview of the principle and its applications
- [Full Text of 10/02 Ballmer Memo](https://www.eweek.com/enterprise-apps/full-text-of-10-02-ballmer-memo/) — Steve Ballmer's 2002 memo referencing the 80/20 rule in Microsoft's strategy

### Related Laws

- [Premature Optimization (Knuth's Optimization Principle)](planning.md#premature-optimization)
- [KISS (Keep It Simple, Stupid)](design.md#kiss-principle)
- [Tesler's Law (Conservation of Complexity)](architecture.md#teslers-law)

---

<a id="cunninghams-law"></a>
## Cunningham's Law

> **Category:** Decisions | **Level:** Junior | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/cunninghams-law/](https://lawsofsoftwareengineering.com/laws/cunninghams-law/)

**The best way to get the correct answer on the Internet is not to ask a question, it's to post the wrong answer.**

### Key Takeaways

- People online love correcting errors. If you’re stuck on a problem, sometimes proposing a solution (even if it might be wrong) can get you to the right solution faster.
- Asking a question might evoke only silence, but confidently stating something (even if incorrect) often provokes a reaction.
- Instead of endlessly asking ‘How should we do X?’, propose a draft or prototype. Even if it’s not entirely correct, having a concrete starting point often gets more feedback (‘No, not like that, do it this way’).

### Overview

Cunningham’s Law arose in the context of online communities, particularly wikis and forums. The underlying observation is that assertions draw more engagement than questions. On Wikipedia, if someone posts incorrect information, other editors will rush in to fix it.

In software engineering, you see this on Stack Overflow and mailing lists. A user asks a question and gets few responses, but if someone posts a slightly wrong answer, others quickly chime in to correct it. By putting something out there, you transform a passive question into an active discussion.

### Examples

A developer stuck on configuring an open-source library posts a question and gets no replies. Using Cunningham’s Law, they post: “For anyone else struggling, the solution is to set ConfigMode to False.” If wrong, someone (possibly the library maintainer) will quickly reply: “Actually, no, you should leave ConfigMode true, it’s another setting you need to change.”

A new developer uncertain about implementing a feature submits a pull request with their best attempt rather than asking in the abstract. Senior engineers review it and point out improvements. By presenting a “proposed answer,” the developer gets the team’s knowledge and ends up with the right approach.

### Origins

Cunningham’s Law is named after Ward Cunningham, the American programmer best known for creating the first wiki software. The actual phrasing of the law is often attributed to a colleague of Cunningham, Steven McGeady, who formulated the adage and named it after Cunningham.

According to McGeady, Ward Cunningham gave him advice in the 1980s regarding early internet forums (Usenet), and McGeady later described it in a comment on a New York Times blog in 2010.

The irony is that Ward Cunningham’s invention, the wiki, is a platform built precisely on the idea that people will collaboratively correct and improve content.

The French have a proverb, “Prêcher le faux pour savoir le vrai” (preach the false to know the true), which captures a similar concept.

### Further Reading

- [The Wiki Way - Bo Leuf & Ward Cunningham](https://en.wikipedia.org/wiki/The_Wiki_Way) — Book about wiki philosophy and collaborative knowledge building
- [How to Ask Questions the Smart Way - Eric S. Raymond](http://www.catb.org/~esr/faqs/smart-questions.html) — Classic guide on effective communication in technical communities
- [Cunningham's Law - Wikipedia](https://meta.wikimedia.org/wiki/Cunningham%27s_Law) — Wikipedia article on the law and its origins

### Related Laws

- [Linus's Law](quality.md#linuss-law)
- [Broken Windows Theory](quality.md#broken-windows-theory)

---
