<pre><font face="Courier" size=-1>&quot;Dr E. Buxbaum&quot; &lt;EB15@le.ac.uk&gt; writes:
<font color="#660066">&gt; 
&gt; Spencer Allain wrote:
&gt; </font>
<font color="#007777">&gt; &gt; The last time I checked the source code for the compiler it sure
&gt; &gt; looked a lot like Modula-3 code, at least for DEC SRC M3 3.6.
&gt; &gt; 
&gt; &gt; What Modula-3 compiler were you examining?</font>
<font color="#660066">&gt; 
&gt; Everything I looked for so far seems to need C++ as companion. I'd
&gt; rather have something self-contained, and I am not too fond of C and its
&gt; derivatives either.</font>

Ahh.... Now I understand.  You've been looking at the Windows 95/NT
installation requirements.  This has to do with the fact that
Microsoft (being the nice people they are) do not ship standard
with the OS a linker or the necessary system libraries to link
applications with during link time.  Hence, for the DEC SRC and
Critical Mass compilers, you need to have Microsoft Visual C or Visual C++
to be installed.

Cambridge Modula-3 (soon to be integrated into Poly Modula-3) use
gnu-win32 for linking on Windows 95/NT machines.  Unfortunately,
the current release of gnu-win32 is still a little buggy.  I'm not
sure what the status of the next release is, but a quick check at
their page still mentions that it may be released in the Fall of
1997 (whatever that means -- I suspect the page hasn't been updated
in a little while)

If Microsoft would release their linker and system libraries for
free, there would be no need for Visual C or Visual C++ for the
current Modula-3 distributions either.

-Spencer
<a target=_top href="http://www.m3.org/">http://www.m3.org/</a></pre>