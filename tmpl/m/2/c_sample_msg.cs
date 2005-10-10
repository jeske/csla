<pre><font face=Courier size=-1>
Recently there have been comments that potential customers need two
independent vendors of Modula3.  It seems to me that requires an
independent implementation.  In the current context it is not clear it
can be done (items 1,2,3).  Alternatively, DEC conveys certain rights
to the worldwide Modula3 community, thus freeing up the potential for
reimplementation (item 4).  In other words, sort of a Linux-style
exercise.

Any feedback, folks?

------------------------------

1. What is an independent implementation?

A new C vendor knows what to provide: An ISO std-compliant compiler
for at least one platform, cpp, make, and interfaces (.h's) and implementations
(.a's) for the std library.  No one would complain about copyright
violation if the vendor coded up the .h's from the std manuals.  

In Modula3 it isn't so straight forward.  Since there isn't an
independent formal standard, we rely on the reference implementation
from DEC.  Each interface is marked with DEC copyright and license.
Even retyping every interface by hand, reordering the elements and
adding your own comments, would still be a copyright violation.

2. What is Modula3 per se?  

What is &quot;Modula3&quot; and what is interesting stuff which happens to be
included in most Modula-3 installations.  My guess is that Modula3 is
defined by:
a) The behavior (look and feel) of the
compiler/m3build/quake/m3makefiles/m3ship
b) The .i3's (and specified behavior) for m3core and libm3.
c) The validation test suite

These are all under DEC copyright and license.  Benign as that may be,
it precludes independent reimplementation.

3. Where is the talent?

I'd guess anyone willing and able to do such a reimplementation has
already at least glanced in the .m3's for m3core and libm3.  So a pure
clean room might be tough to establish.  An implementation in Modula3
is almost sure to have copyright violations.  An implementation in
another language might pass.  (E.g., doing the implementation in java,
ada, or c might constitute reimplementaiton instead of
&quot;translation&quot;).</pre> 

<p><i><a href=/groups?hl=en&lr=&ie=UTF-8&oe=UTF-8&safe=off&selm=r9k9eet050.fsf%40pigpen.ca.boeing.com&rnum=1 target=_top>Read the rest of this message...</a> (21 more lines)</i><p><a name="link2"></a>
