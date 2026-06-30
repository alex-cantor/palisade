# palisade

A mock CCDC environment generator, to quickly spin up networks on PVE for realistic adversarial simulation

## About

Ask any CCDC competitor the best way to get good, and their answer will be the same: get experience. It is really hard to do this through only competitions, as there are only a couple of competitions per year. The best way to do this is through mock competitions, so I knew I wanted to build infrastructure to set up mock competitions fast.

I also knew I wanted to have the environment replicate CCDC environments as best as possible. Originally, I was going to provision credentials for my teammates, but one of my teammates (@lolmenow) told me about a portal he was writing to replicate the eCitadel environment--which is very similar to the CCDC environment. I thought this was an awesome idea, so I plan to replicate it. For the project, I think it would be best for there to be three general components: the mock environment generator itself, the CCDC-like interface, and the autonomous red teamer. I'll discuss each in more depth later

Due to the nature of this project (and CCDC itself), I am also excited for potential applications outside of CCDC. In volunteering with the Iowa Air National Guard, I was tasked with helping to configure, deploy, and pentest a vulnerable network for the military personnel to then watch logs. By being able to spin up a network as I will eventually be able to do with palisade, this task will become trivial. In addition to the defensive side, networks could be spun up for practice with red teaming and pentesting.

> Disclosure: I already had access to a ProxMox (PVE) server with root permissions and a ton of resources (70TB of usable storage plus 1/2 PB sitting, waiting to be plugged in) so I was starting off at a better point than most competitors. That said, you should be able to replicate this project via a service like Hetzner or OVHCloud for less than $100/month.
