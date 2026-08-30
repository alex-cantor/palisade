# Palisade: Interface Me (part 6)

## What / Why An Interface?

Looking back, this component of the project is very obvious. But, originally, I was not going to write an interface--at least, not a graphical interface (website) as is the case now. My original plan was to simply have a CLI (or even a TUI, if I was feeling spicy). This was largely as the original plan was just to have the tool spin up networks. Now, since palisade has the ability to simulate CCDC environments (including viewing announcements, submitting injects, etc)--and because I wanted the tool to be used by brand new CCDC teams, I chose to write a GUI.

The inspiration from the design must be credited to @lolmenow (my CCDC teammate), CCDC, and eCitadel.

To credit more precisely, a technology choice (and the idea of building something like this in general) should be credited to @lolmenow; when chatting with him, he mentioned he was working on a project where he utilized the resources from two laptops in running a PVE server, then wrote an interface with Apache Guacamole on https://portal.sakouk.me for anyone to request an account and then access the PVE server. I thought this sounded awesome, so I knew I wanted to utilize Apache Guacamole in this type of interface.

With the goal of making the environment CCDC-like practice for my team (and to simply pull on ideas for how the interface should look), I turned to CCDC (of course) and eCitadel. I looked through the internet and found screenshots of the dashboard, which played a major role in how I designed the pages.

Shoutouts go to Quotient and Ludus as well, as there is a likelihood I will take ideas from them.

## Getting Into It

Ok, enough of an introduction. I am going to split this into three categories: the competitor view, the organizer view, and the sysadmin view.

### The Competitor View

#### Login

As will be mentioned shortly, there is no signup feature for competitors. Their credentials must be provisioned for them.

Regardless, on the login screen (eg. while unauthenticated), anyone can view the scoreboard and uptime, although they can not review any competition-specific info. To access competition-specific info (including announcements, injects, etc), competitors can simply log in with the credentials they were provided prior to competition start. Access to competition-specific info will be released after authentication on a time-based schedule, as is chosen by the organizer(s).

#### Dashboard

On the dashboard, competitors have access to view **Announcements** and **Injects**. Announcements simply include the announcement text and date/time it at which it was published. I am considering adding a "read" ability, but that is a future enhancement--not something I am concerned about now. Injects include the title, start time, due time, points awarded, and the ability to upload a file as the inject submission. A possible enhancement hear is a text or rich text box without needing to upload a file, but as all injects should be responded to in a professional format, I do not see that as a high priority.

TODO: insert an image here
#### Scoreboard

#### Uptime



#### VMs

On the VMs page, competitors have access to start, stop, reboot, revert snapshots (conditionally), and view each machine. Two of these points are unclear, so let me clarify. When I say they can revert snapshots (conditionally), I mean they can revert each VM to the base snapshot up to as many times as the organizer specifies. The default number of reverts is 10, although this number is just a default--it very well may be changed (and communicated) from competition to competition. In terms of viewing each VM, while the VMs can be connected to remotely, they may also be managed in the web interface--via Apache Guacamole.

### The Organizer View

#### Provision Environment

#### Inject Management

There are a few critical things an organizer must do:
1. **Provision competition environments**
	1. Numbers of teams/team members and associated credentials
	2. Difficulty of the network
	3. Difficulty of the injects
	4. Aggression of the autonomous Red Teamer
2. Respond to injects

## The Sys-Admin View

This is the person in charge of setting up `palisade` itself. They'll follow the instructions in the `README.md`.