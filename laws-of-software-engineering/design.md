# Laws of Software Engineering — Design

Extracted from [Laws of Software Engineering](https://lawsofsoftwareengineering.com/). This document covers all **6** principles categorized under **Design**.

## Table of Contents

- [YAGNI (You Aren't Gonna Need It)](#yagni) — *Don't add functionality until it is necessary.* (Junior)
- [DRY (Don't Repeat Yourself)](#dry-principle) — *Every piece of knowledge must have a single, unambiguous, authoritative representation.* (Junior)
- [KISS (Keep It Simple, Stupid)](#kiss-principle) — *Designs and systems should be as simple as possible.* (Junior)
- [SOLID Principles](#solid-principles) — *Five main guidelines that enhance software design, making code more maintainable and scalable.* (Mid)
- [Law of Demeter](#law-of-demeter) — *An object should only interact with its immediate friends, not strangers.* (Mid)
- [Principle of Least Astonishment](#principle-of-least-astonishment) — *Software and interfaces should behave in a way that least surprises users and other developers.* (Mid)

---

<a id="yagni"></a>
## YAGNI (You Aren't Gonna Need It)

> **Category:** Design | **Level:** Junior | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/yagni/](https://lawsofsoftwareengineering.com/laws/yagni/)

**Don't add functionality until it is necessary.**

### Key Takeaways

- YAGNI is here to remind developers to focus on current tasks rather than implementing features that aren’t needed now.
- Anticipating future needs often leads to over-engineering, and this adds complexity and maintenance issues.
- YAGNI encourages iterative development. You implement minimal solutions and refine or extend them when needed.

### Overview

YAGNI captures a core philosophy of agile development: don’t write code for features that haven’t been requested or aren’t immediately needed.

If you’re implementing Module A and think “in the future we might need Module B to do X, so I’ll code some hooks for that now,” YAGNI advises against it because that future feature may never come or may change drastically.

This principle directly fights over-engineering. To apply YAGNI successfully, teams rely on confidence in refactoring. You defer a feature only if you trust you can add it later at low cost.

Agile methods provide that safety net via good test coverage, refactoring tools, and continuous integration. YAGNI pushes the problem of complexity to when it’s actually needed.

### Examples

You’re building a feature with specific behavior. You think “maybe in the future someone will want to toggle this on/off, so I’ll add a configuration flag now.” YAGNI challenges that. Unless there’s a current requirement for configurability, implement only expected behavior, nothing more.

You’re working on a library function that currently does one thing. You realize it might be useful more generally, so you might add parameters or abstraction tiers. YAGNI says implement it for the original task.

Your app needs JSON export? Implement simple JSON, not a full serialization library supporting XML, YAML, etc.

Teams that adopt YAGNI are often comfortable refactoring because they trust that when the feature set grows, they’ll have more information about real use cases, leading to better abstractions.

### Origins

YAGNI was part of the Extreme Programming (XP) paradigm in the late 1990s. It was promoted by Ron Jeffries, one of XP’s founders, who wrote: “Always implement things when you actually need them, not when you just foresee that you need them.”

The slogan was adopted in XP literature, such as Extreme Programming Installed (2001).

### Further Reading

- [YAGNI on Martin Fowler's website](https://martinfowler.com/bliki/Yagni.html) — Clear explanation with practical examples
- [Extreme Programming Installed](https://amzn.to/4siycbq) — Ron Jeffries, Ann Anderson, Chet Hendrickson
- [You Aren't Gonna Need It on C2 Wiki](http://wiki.c2.com/?YouArentGonnaNeedIt) — Original XP community discussion

### Related Laws

- [KISS (Keep It Simple, Stupid)](#kiss-principle)
- [DRY (Don't Repeat Yourself)](#dry-principle)
- [Premature Optimization (Knuth's Optimization Principle)](planning.md#premature-optimization)

---

<a id="dry-principle"></a>
## DRY (Don't Repeat Yourself)

> **Category:** Design | **Level:** Junior | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/dry-principle/](https://lawsofsoftwareengineering.com/laws/dry-principle/)

**Every piece of knowledge must have a single, unambiguous, authoritative representation.**

### Key Takeaways

- The DRY principle is about avoiding duplication of knowledge in code. If the same idea or logic is in multiple places, it’s a signal to refactor.
- When requirements change, you should update logic in only one place. Repeated code increases the risk of inconsistencies and bugs (you might fix a bug in one copy and forget about the others).
- Be careful to apply DRY wisely. It’s about knowledge repetition, not just duplication. Sometimes two pieces of code look alike but do different jobs; merging them could over-complicate things.

### Overview

The idea of DRY is simple: each fact or piece of logic in your system should be expressed once and only once. If you find the same code, formula, or rule in multiple modules, you’re violating DRY. Such repetition creates hidden maintenance cost. When the business rule changes, you must hunt down every duplicate instance.

By following DRY, developers strive for a single, unique implementation of any given behavior. This often means abstracting common code into a function or class, or consolidating configuration into a single file.

DRY also applies to database schemas, tests, and documentation.

However, remember that DRY is about duplicated intent, not just similar-looking code. Two pieces of code can look identical but serve different purposes in an application.

### Examples

An application has a database connection URL in five different source files. If the database host changes, you’d have to edit all five places. The DRY approach keeps that URL in a single configuration variable that all modules read.

If two parts of an app both format dates the same way, create a single `formatDate()` utility function and call it from both places. Now if the date format needs to change, there’s precisely one function to modify.

Large codebases benefit from DRY through shared libraries. If multiple applications need the same security logic, create a shared library instead of copying code across applications.

### Origins

The term “DRY” was coined in 1999 by Andy Hunt and Dave Thomas in their book The Pragmatic Programmer. They defined it as: “Every piece of knowledge must have a single, unambiguous, authoritative representation within a system.”

Even earlier, avoiding code duplication was part of structured programming and the Unix philosophy. In Extreme Programming, a similar idea was known as “Once and Only Once.” Hunt and Thomas gave it a catchy name and expanded its scope beyond just code to all information.

### Further Reading

- [The Pragmatic Programmer, 20th Anniversary Edition](https://amzn.to/4piJutH) — The original source of the DRY principle by Hunt and Thomas
- [DRY - Wikipedia](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself) — Overview of the principle and related concepts
- [Code Complete](https://amzn.to/3N57T8t) — Steve McConnell's guide covering code duplication and abstraction

### Related Laws

- [SOLID Principles](#solid-principles)
- [Law of Demeter](#law-of-demeter)

---

<a id="kiss-principle"></a>
## KISS (Keep It Simple, Stupid)

> **Category:** Design | **Level:** Junior | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/kiss-principle/](https://lawsofsoftwareengineering.com/laws/kiss-principle/)

**Designs and systems should be as simple as possible.**

### Key Takeaways

- KISS primarily refers to avoiding complexity in solution designs. A solution that satisfies the requirement and is simple in design is better than a complex one.
- Simple code is easier and faster to understand and debug. It’s even easier to understand and fix if you’re your own future self. Smarter code may look impressive at first, but it often masks problems.
- The code solution should be as simple as possible. Anything that adds complexity unnecessarily is counter to the KISS Principle.

### Overview

The KISS principle is a reminder that simplicity should be a key goal. If you can solve a problem with a 50-line script versus a complex 500-line solution, KISS favors the 50-line solution because each line of code has the potential to cause an error.

Why is simplicity so important? Software has to be understood by humans. A simple design is much easier to maintain: new team members can get up to speed faster, bugs are easier to localize, and modifications cause fewer ripple effects.

The KISS principle encourages developers to resist “clever” code that does too much at once, and to avoid architecting solutions that address future problems at the cost of current complexity.

### Examples

A web application needs to generate reports. A KISS approach would use a simple script or existing library to query the database and output a CSV. A non-KISS approach would design a complete plug-in architecture “just in case” you need it more generically later. If requirements are small, the latter is overkill.

When writing a function to parse a file, a KISS implementation uses simple logic: open the file, read line by line, split fields, handle errors. A complex approach might implement a fully generic parser-combinator framework. Unless you truly need that generality, the simpler approach will be easier to get right and maintain.

Many experienced engineers advise: “First make it work, then make it right, then make it fast (if needed).”

### Origins

The phrase “Keep It Simple, Stupid” came from the U.S. military. It’s attributed to Kelly Johnson, a lead engineer at Lockheed’s Skunk Works in the 1960s. Johnson challenged his team: design an aircraft that could be repaired with basic tools by an average mechanic in the field.

Influential programmers such as Edsger Dijkstra and C.A.R. Hoare often discussed complexity. Hoare said, “There are two ways of constructing a software design: One way is to make it so simple that there are obviously no deficiencies, and the other way is to make it so complicated that there are no obvious deficiencies. The first method is far more difficult.”

The KISS principle has since become a cornerstone of software engineering best practices.

### Further Reading

- [A Philosophy of Software Design](https://amzn.to/3N1uR0f) — John Ousterhout's book on managing complexity in software
- [KISS Principle - Wikipedia](https://en.wikipedia.org/wiki/KISS_principle) — Overview of the principle and its origins
- [Code Complete](https://amzn.to/3N57T8t) — Steve McConnell's practical handbook emphasizing simplicity in code

### Related Laws

- [YAGNI (You Aren't Gonna Need It)](#yagni)
- [Principle of Least Astonishment](#principle-of-least-astonishment)
- [Gall's Law](architecture.md#galls-law)

---

<a id="solid-principles"></a>
## SOLID Principles

> **Category:** Design | **Level:** Mid | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/solid-principles/](https://lawsofsoftwareengineering.com/laws/solid-principles/)

**Five main guidelines that enhance software design, making code more maintainable and scalable.**

### Key Takeaways

- Following SOLID leads to software that is easier to extend, test, and refactor without breaking existing functionality. Each principle addresses a different aspect of good OO design.
- A class with a single responsibility (SRP) that depends on well-defined interfaces (ISP, DIP) and uses inheritance appropriately (LSP) and polymorphism for extensions (OCP) will likely be easy to maintain.
- Changes to one part of the system won’t cascade into breakages elsewhere, because the code is loosely coupled and well-encapsulated.
- SOLID does not guarantee a perfect design, but it provides proven guidelines for object-oriented programming.

### Overview

The SOLID principles are five high-level guidelines for object-oriented design: **Single Responsibility** (one concern per class), **Open/Closed** (open for extension, closed for modification), **Liskov Substitution** (subclasses must be substitutable for their parent), **Interface Segregation** (no forced dependency on unused interfaces), and **Dependency Inversion** (depend on abstractions, not concretions).

When applied together, these principles produce systems that are modular, extensible, and robust under change. Code becomes easier to test, refactor, and extend without breaking existing functionality.

### Examples

For the **Single Responsibility Principle**, consider a web application managing user accounts. An anti-SRP design might have a single `UserManager` class handling validation, database operations, sending emails, and logging. A better design separates these into `UserValidator`, `UserRepository`, `EmailService`, and a `UserRegistrationService` that orchestrates them. Each class has one focus, and if the email format changes, you only touch `EmailService`.

For the **Dependency Inversion Principle**, imagine a `NotificationService` that sends alerts. Without DIP, it directly uses `EmailSender` or `SMSSender`. With DIP, you define an `INotificationChannel` interface, and all senders implement it. The service depends only on the abstraction, making it easy to add new channels or swap in test doubles.

### Origins

The five SOLID principles emerged over the years and were collected and popularized by Robert C. Martin (Uncle Bob). The acronym SOLID was coined around 2004 by Michael Feathers, who noticed the initial letters spelled out a catchy word.

Uncle Bob described SRP, OCP, LSP, ISP, and DIP in various articles from the late 1990s and early 2000s, including his “Principles of Object-Oriented Design” papers and his 2002 book Agile Software Development: Principles, Patterns, and Practices. These principles drew from earlier thinkers: OCP from Bertrand Meyer (1988), LSP from Barbara Liskov (1987), ISP from work at Xerox PARC, and DIP and SRP were Martin’s formulations inspired by layering and cohesion practices.

### Further Reading

- [Design Principles and Design Patterns](https://web.archive.org/web/20150906155800/http://www.objectmentor.com/resources/articles/Principles_and_Patterns.pdf) — Robert C. Martin's foundational paper on OO design principles
- [Agile Software Development: Principles, Patterns, and Practices](https://amzn.to/497oH7H) — Uncle Bob's comprehensive book introducing SOLID principles
- [Clean Architecture](https://amzn.to/4jeeN7k) — Robert C. Martin's guide to software architecture and design
- [SOLID - Wikipedia](https://en.wikipedia.org/wiki/SOLID) — Overview of all five principles with examples
- [Design Patterns: Elements of Reusable Object-Oriented Software](https://amzn.to/3LnM5o6) — The Gang of Four's classic on OO patterns that complement SOLID

### Related Laws

- [Law of Demeter](#law-of-demeter)
- [Hyrum's Law](architecture.md#hyrums-law)
- [The Law of Leaky Abstractions](architecture.md#law-of-leaky-abstractions)
- [DRY (Don't Repeat Yourself)](#dry-principle)
- [KISS (Keep It Simple, Stupid)](#kiss-principle)
- [YAGNI (You Aren't Gonna Need It)](#yagni)

---

<a id="law-of-demeter"></a>
## Law of Demeter

> **Category:** Design | **Level:** Mid | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/law-of-demeter/](https://lawsofsoftwareengineering.com/laws/law-of-demeter/)

**An object should only interact with its immediate friends, not strangers.**

### Key Takeaways

- An object should only call methods of: itself, its direct components, its function parameters, or objects it creates. It should not navigate through one object to reach another (‘don’t talk to strangers’).
- If object A only calls B (its immediate friend) and doesn’t reach into B’s internals (like C), then changes to C or removal of C don’t affect A. Each class knows as little as possible about others, reducing the impact of changes
- It often leads to adding wrapper methods or delegations. While that might increase the number of methods, it results in cleaner interactions.

### Overview

The Law of Demeter, also known as “don’t talk to strangers” or the “principle of least knowledge,” was formulated to minimize the knowledge that any given object has about the overall system structure.

In practice, if object A has a reference to object B, and B has a reference to C, A should not call methods on C through B (like `a.b.getC().doSomething()`). A can talk to B, and B can talk to C, but A shouldn’t directly get involved with C.

This fosters loose coupling. If you break LoD, your code assumes the structure extends beyond its immediate neighbors. For example, if `OrderProcessor` does `order.getCustomer().getAddress().getZipCode()`, it knows that an Order has a Customer with an Address. If Customer is changed to have multiple addresses, OrderProcessor breaks. If instead Order had a method `getShippingZip()` that internally navigates its customer/address, OrderProcessor could call that and be oblivious to structural changes.

LoD aligns with information hiding: each object hides its internals and only exposes necessary interfaces.

### Examples

Consider a `Presenter` object with a reference to a UI View containing a `TextField`. Without LoD, the presenter might do `view.getTextField().setText("Hello")`. LoD encourages View to provide `setUserMessage(String)`, internally calling `textField.setText`. The Presenter doesn’t need to know there’s a TextField specifically. If later the View uses a Label instead, the Presenter code doesn’t change.

You can identify violations by counting dots: `a.getB().getC().doSomething()` has two dots, one too many. A single dot `a.doSomething()` or at most `a.getB().doSomething()` is preferable.

By adhering to LoD, each component remains more self-contained, and systems become a network of “friends” rather than a tangle of strangers reaching through each other.

### Origins

The Law of Demeter was first described around 1987 by Ian Holland and colleagues at Northeastern University as part of the Demeter Project on adaptive and aspect-oriented software development. It’s named after the project, which itself was named after the Greek goddess of agriculture, signifying a “growing” approach to software.

The researchers, including Karl Lieberherr, sought ways to make software more maintainable and developed this style rule. They summarized it with the motto “Only talk to your friends.”

### Further Reading

- [Object-Oriented Programming: An Objective Sense of Style](https://www2.ccs.neu.edu/research/demeter/papers/law-of-demeter/oopsla88-law-of-demeter.pdf) — Original paper by Lieberherr, Holland, and Riel
- [Law of Demeter - Wikipedia](https://en.wikipedia.org/wiki/Law_of_Demeter) — Overview of the principle with examples
- [The Paperboy, The Wallet, and The Law Of Demeter](https://www2.ccs.neu.edu/research/demeter/demeter-method/LawOfDemeter/paper-boy/demeter.pdf) — Introduction paper by David Bock with the famous Paperboy example
- [Design Patterns: Elements of Reusable Object-Oriented Software](https://amzn.to/3LnM5o6) — The Gang of Four book with patterns that enforce loose coupling

### Related Laws

- [SOLID Principles](#solid-principles)
- [The Law of Leaky Abstractions](architecture.md#law-of-leaky-abstractions)
- [Hyrum's Law](architecture.md#hyrums-law)
- [KISS (Keep It Simple, Stupid)](#kiss-principle)

---

<a id="principle-of-least-astonishment"></a>
## Principle of Least Astonishment

> **Category:** Design | **Level:** Mid | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/principle-of-least-astonishment/](https://lawsofsoftwareengineering.com/laws/principle-of-least-astonishment/)

**Software and interfaces should behave in a way that least surprises users and other developers.**

### Key Takeaways

- Design decisions should align with user expectations. When someone uses a component (a UI element, API, etc.), its behavior should not be surprising or counterintuitive.
- Following platform norms or standard conventions yields the least astonishment.
- In practice, it improves usability and developer experience. Users can predict how to interact with the software, and developers can predict how to use an API by analogy with similar ones. Surprises often lead to mistakes.

### Overview

The Principle of Least Astonishment (POLA) is a general design principle in user interface design, software API design, coding, and documentation. The idea is simple: don’t surprise the user.

The system should behave in a way that matches the user’s mental model of how it ought to work. Violating this principle doesn’t necessarily break functionality, but it breaks trust and ease of use.

In coding, this principle states that your code should behave as the developer expects when name, type, and context are taken into account. We should choose defaults and behaviors that match standard conventions and avoid “surprise” side effects.

### Examples

In software APIs, POLA means designing functions and behaviors that meet standard expectations. If you have a method `deleteFile()`, one would expect it to remove the file. It should not secretly archive it or throw an error if the file doesn’t exist.

If your method works similarly to a well-known one in another library, keep naming and behavior aligned. A `toString()` method should return human-readable text, not a binary blob.

POLA also covers error handling and defaults. Sensible defaults cause the least surprise. For developers, code surprises are equally problematic. If a function `parseDate(str)` internally modifies a global date format setting, that’s surprising.

Following standard naming conventions matters: a variable named `isReady` should be boolean, a function named `compute` should return something rather than modify global state.

A delighted user or developer uses something and it “just works” as expected.

### Origins

The concept of least astonishment has roots in early human-computer interaction. An early mention appears in PL/I programming language documentation around 1967, complaining that certain behaviors violated the “law of least astonishment.”

The principle was explicitly stated in a 1972 publication on programming language design, recommending that language constructs behave as their syntax suggests and follow widely accepted conventions.

Since then, it has been emphasized across various domains. In the Unix community, Eric Raymond’s Art of Unix Programming references it as the “Rule of Least Surprise.”

### Further Reading

- [The Art of Unix Programming](https://amzn.to/4q4uTTY) — Eric S. Raymond's book including the Rule of Least Surprise
- [How to Design a Good API and Why it Matters](https://www.youtube.com/watch?v=aAb7hSCtvGw) — Joshua Bloch's talk on API design principles
- [Principle of Least Astonishment - Wikipedia](https://en.wikipedia.org/wiki/Principle_of_least_astonishment) — Overview of the principle with history and examples

### Related Laws

- [Hyrum's Law](architecture.md#hyrums-law)
- [KISS (Keep It Simple, Stupid)](#kiss-principle)
- [Postel's Law](quality.md#postels-law)
- [Law of Demeter](#law-of-demeter)

---
