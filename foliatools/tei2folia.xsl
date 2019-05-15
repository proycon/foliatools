<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
   xmlns:folia="http://ilk.uvt.nl/folia"
   xmlns:edate="http://exslt.org/dates-and-times"
   xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
   xmlns:tei="http://www.tei-c.org/ns/1.0"
   xmlns:xlink="https://www.w3.org/1999/xlink"
   xmlns:postprocess="http://postprocessor.placeholder"
   exclude-result-prefixes="tei edate xlink" version="1.0"
   xmlns="http://ilk.uvt.nl/folia"
   xpath-default-namespace="http://www.tei-c.org/ns/1.0">

  <xsl:output method="xml" indent="yes"/>
<!--
  <xsl:strip-space elements="*"/>
-->

<xsl:param name="linesAsP">false</xsl:param>
<xsl:strip-space elements="l p interp meta interpGrp"/>
<xsl:param name="docid"><xsl:value-of select="//publicationStmt/idno/text()"/></xsl:param>

<!-- disabled (proycon)
<xsl:param name="pid0"><xsl:value-of select="//interpGrp[@type='pid']/interp/text()"/></xsl:param>
<xsl:param name="pid"><xsl:value-of select="replace($pid0,'.*_','')"/></xsl:param>
<xsl:param name="pidplus0"><xsl:value-of select="//interpGrp[@type='corpusProvenance']/interp/text()"/>-1-1_<xsl:value-of select="$pid"/></xsl:param>
<xsl:param name="pidplus"><xsl:message>PID::::::<xsl:value-of select="$pidplus0"/></xsl:message><xsl:value-of select="replace($pidplus0,' ','')"/></xsl:param>
-->


<xsl:template name="note-resp">
<xsl:if test="@resp">
<xsl:attribute name="class">resp_<xsl:value-of select="@resp"/></xsl:attribute>
</xsl:if>
</xsl:template>

<xsl:template name="copy-attributes">
    <xsl:for-each select="@*">
        <xsl:attribute name="{name(.)}"><xsl:value-of select="."/></xsl:attribute>
    </xsl:for-each>
</xsl:template>

<xsl:template name="metadata_link">
  <xsl:variable name="inst"><xsl:value-of select="./@xml:id"/></xsl:variable>
  <xsl:if test="//interpGrp[@inst=concat('#',$inst)]">
   <xsl:attribute name="metadata"><xsl:value-of select="./@xml:id"/></xsl:attribute>
  </xsl:if>
</xsl:template>

<xsl:param name='generateIds'>true</xsl:param>
<xsl:param name='useCorrectionTags'>true</xsl:param>

<xsl:template name="setId">
 <xsl:if test="@xml:id or $generateIds='true'">
    <xsl:attribute name="xml:id">
        <xsl:choose>
            <xsl:when test="@ID"><xsl:value-of select="@xml:id"/></xsl:when>
            <xsl:otherwise>e<xsl:number level="any" count="*"/></xsl:otherwise>
        </xsl:choose>
    </xsl:attribute>
 </xsl:if>
</xsl:template>

<!-- specialPara's like quote are ugly! -->

<xsl:template name="specialPara">
<p class="{name(.)}">
<t>
<xsl:apply-templates select=".//text()"/>
</t>
</p>
</xsl:template>

<xsl:template match="quote[not(ancestor::p)]">
<xsl:call-template name="specialPara"/>
</xsl:template>

<!--
 text nodes, inline tags en ignorable tagging binnen t.
  Let op: extra if ook in dergelijke andere templates toevoegen
  Of liever parametriseren
-->

<!-- meer algemeen iets met inline elementen doen wat je hier met hi en name doet -->

<xsl:template name="pContents">
<xsl:if test="node()[not(self::note or self::add)]">
<t>
<xsl:apply-templates select="node()[not(self::note or self::add or self::signed)]|signed/text()|signed/name|signed/hi"/>
</t>
</xsl:if>
<!--<xsl:apply-templates select="node()[self::note]"/> -->
</xsl:template>

<!-- gezeur met content van cell die gedeeltelijk in p zit -->

<xsl:template name="pContentsPlus">
    <xsl:if test="node()[not(self::note or self::add)]">
<t>
<xsl:apply-templates select="p/node()[not(self::note or self::add or self::signed)]|node()[not(self::note or self::p or self::add or self::signed)]|signed/text()|signed/name|signed/hi"/>
</t>
    </xsl:if>
    <!--<xsl:apply-templates select="node()[self::note]"/> -->
</xsl:template>

<xsl:template name="pLike">
    <xsl:text>
    </xsl:text>
    <p>
    <xsl:if test="name(.) != 'p'">
        <desc><xsl:value-of select="name(.)" /></desc>
    </xsl:if>
    <xsl:call-template name="pContents"/>
    <xsl:apply-templates select="./signed/*[not(self::hi or self::name)]"/>
    </p>
    <xsl:apply-templates select="./note|./add"/>
</xsl:template>

<!-- probleem: p binnen note wil niet -->
<xsl:template match="note">
<note n="{@xml:id}">
<xsl:call-template name="note-resp"/>
<t>
<xsl:apply-templates/>
</t>
</note>
</xsl:template>

<xsl:template match="note" mode="nonotes"><t-gap class="note_ref" n="{@xml:id}" xlink:href="TODO"/></xsl:template>

<xsl:template match="note[./table]">
<note>
<xsl:attribute name="xml:id">TODO</xsl:attribute>
<xsl:call-template name="note-resp"/>
<xsl:message>PAZOP tabel in noot: <xsl:value-of select="."/></xsl:message>
<xsl:if test="node()[following-sibling::table and not(self::table)]">
<t>
<xsl:apply-templates select="node()[following-sibling::table and not(self::table)]"/>
</t>
</xsl:if>
<xsl:apply-templates select="./table"/>
<xsl:if test="node()[preceding-sibling::table and not(self::table)]">
<t>
<xsl:apply-templates select="node()[preceding-sibling::table and not(self::table)]"/>
</t>
</xsl:if>
</note>

</xsl:template>

<xsl:template match="note//note">
<xsl:apply-templates/>
</xsl:template>

<xsl:template match="item">
<item>
<t>
<xsl:apply-templates/>
</t>
</item>
</xsl:template>


<xsl:template match="list">
<list>
<xsl:apply-templates/>
</list>
</xsl:template>

<xsl:template match="q">
<quote>
<xsl:apply-templates/>
</quote>
</xsl:template>

<!--
<xsl:template match="l">
<p class='l' xml:id="{fun:makeId(.)}">
<t>
<xsl:apply-templates/>
</t>
</p>
</xsl:template>
-->

<!--
Behandeling van l als peetje kan niet echt.
beter
<lg>
<head>

<t>
<t-str class='line'></t-str>
.....
</t>

<note>
<note>
<note>
</lg>

met anchors voor de notes (die niet in t mogen)
-->

<xsl:template match="lg">
    <xsl:text>
    </xsl:text>
    <div>
    <xsl:attribute name="class"><xsl:choose><xsl:when test="@type"><xsl:value-of select="@type" /></xsl:when><xsl:otherwise>linegroup</xsl:otherwise></xsl:choose></xsl:attribute>
    <xsl:choose>
        <xsl:when test="$linesAsP='true'">
            <xsl:apply-templates/>
        </xsl:when>
        <xsl:otherwise>
            <div class="linegroup">
            <t><xsl:apply-templates select="l"/></t>
            </div>
            <xsl:apply-templates select=".//note"/>
        </xsl:otherwise>
    </xsl:choose>
    </div>
</xsl:template>

<xsl:template match="epigraph">
    <div class="epigraph">
        <xsl:apply-templates/>
    </div>
</xsl:template>



<xsl:template match="signed">
<xsl:apply-templates/>
</xsl:template>


<!-- toegevoegd voor beaufort: geen p's binnen note doorlaten -->

<xsl:template match="note//p"><xsl:apply-templates/></xsl:template>

<!--
<xsl:template match="l">
</xsl:template>
-->

<xsl:template match="l">
<xsl:choose>
  <xsl:when test="$linesAsP='true'">
   <xsl:call-template name="pLike"/>
  </xsl:when>

  <xsl:otherwise>
    <xsl:choose>
      <xsl:when test="parent::lg">
          <t-str class="l"><xsl:if test="@n"><xsl:attribute name="n"><xsl:value-of select="@n" /></xsl:attribute></xsl:if><xsl:apply-templates select="node()[not (self::note)]"/></t-str><br class='poetic.linebreak'><xsl:if test="@n"><xsl:attribute name="n"><xsl:value-of select="@n" /></xsl:attribute></xsl:if><xsl:text>&#10;</xsl:text></br>
      </xsl:when>
      <xsl:otherwise>
        <xsl:choose>
          <xsl:when test="name(preceding-sibling::*[1])='l'"></xsl:when>
          <xsl:otherwise>
             <xsl:variable name="cur"><xsl:value-of select="."/></xsl:variable>
             <part class='lg.artefact'>
                 <t><t-str class="line"><xsl:if test="@n"><xsl:attribute name="n"><xsl:value-of select="@n" /></xsl:attribute></xsl:if><xsl:apply-templates mode='nonotes'/></t-str><br class='poetic.linebreak'><xsl:if test="@n"><xsl:attribute name="n"><xsl:value-of select="@n" /></xsl:attribute></xsl:if></br>
                  <xsl:text>&#10;</xsl:text>
                  <xsl:for-each select="following-sibling::l[name(preceding-sibling::*[1])='l'][preceding-sibling::l[not(name(preceding-sibling::*[1])='l')][1]=$cur]">
                      <t-str class="line"><xsl:if test="@n"><xsl:attribute name="n"><xsl:value-of select="@n" /></xsl:attribute></xsl:if><xsl:apply-templates mode='nonotes'/></t-str><br class='poetic.linebreak'><xsl:if test="@n"><xsl:attribute name="n"><xsl:value-of select="@n" /></xsl:attribute></xsl:if></br><!-- filter out notes -->
                   <xsl:text>&#10;</xsl:text>
                  </xsl:for-each>
                </t>
             </part>
             <!-- still need to collect the notes -->
             <xsl:for-each select=".//note"><xsl:apply-templates select="."/></xsl:for-each>
             <xsl:for-each select="following-sibling::l[name(preceding-sibling::*[1])='l'][preceding-sibling::l[not(name(preceding-sibling::*[1])='l')][1]=$cur]">
                <xsl:for-each select=".//note"><xsl:apply-templates select="."/></xsl:for-each>
             </xsl:for-each>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:otherwise>
</xsl:choose>
</xsl:template>

<xsl:template match="p|speaker|trailer|closer|opener|lxx">
<xsl:call-template name="pLike"/>
</xsl:template>

<xsl:template match="p//quote">
<t-str class='quote'>
<xsl:apply-templates/>
</t-str>
</xsl:template>

<xsl:template match="name">
<xsl:apply-templates/>
</xsl:template>

<xsl:template match="figure">
<figure>
<xsl:if test="xptr">
<xsl:attribute name="src"><xsl:value-of select="xptr/@to" /></xsl:attribute>
</xsl:if>
<xsl:apply-templates select="figDesc"/>
</figure>
</xsl:template>

<xsl:template match="figDesc">
<caption>
<xsl:call-template name="textandorstructure"/>
</caption>
</xsl:template>

<!-- figure out if we need a text node -->
<xsl:template name="textandorstructure">
    <xsl:choose>
        <xsl:when test="text()|hi|pb">
            <xsl:choose>
                <xsl:when test="p|div|s|lg|sp|table|row|cell|figure|list|item">
                    <!-- there are structural elements as well, we need to make sure they don't end up in <t> -->
                    <t><xsl:apply-templates select="text()|hi" /></t>
                    <!-- TODO -->
                </xsl:when>
                <xsl:otherwise>
                    <t><xsl:apply-templates /></t>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:when>
        <xsl:when test="p|div|s|lg|sp|table|row|cell|figure|list|item">
            <!-- structure only, easy -->
            <xsl:apply-templates/>
        </xsl:when>
    </xsl:choose>
</xsl:template>


<!-- noten gaan hier verloren -->

<!-- disabled XSLT 2.0 (proycon)
<xsl:template match="p[./table|./figure|./list]|xcloser[./list]|xcloser[./signed/list]">
<xsl:for-each-group select="node()" group-ending-with="table">
<p>
<t><xsl:apply-templates select="current-group()[not(self::table or self::figure or self::list or self::signed)]"/></t>
</p>
<xsl:apply-templates select="current-group()[self::table or self::figure or self::list or self::signed]"/>
</xsl:for-each-group>
</xsl:template>
-->


<xsl:template match="docTitle/titlePart"><xsl:apply-templates/></xsl:template>

<!-- niet aan note binnen head gedacht -->

<xsl:template match="head|docTitle|titlePart[not(ancestor::docTitle)]">
<head>
<xsl:call-template name="textandorstructure"/>
</head>
</xsl:template>

<xsl:template match="note">
<postprocess:note n="{@n}" place="{@foot}"><xsl:value-of select="text()" /></postprocess:note>
</xsl:template>

<xsl:template match="cell">
    <cell>
        <p>
            <xsl:call-template name="haalPbBinnenInCel"/>
            <xsl:call-template name="pContentsPlus"/>
        </p>
    </cell>
</xsl:template>


<!--
<xsl:template match="cell[./p]">
<xsl:element name="{name(.)}">
<xsl:call-template name="haalPbBinnenInCel"/>
<xsl:attribute name="xml:id"><xsl:value-of select="fun:makeId(.)"/></xsl:attribute>
<xsl:apply-templates/>
</xsl:element>
</xsl:template>
-->

<xsl:template match="table|row">
<xsl:element name="{name(.)}">
<xsl:apply-templates/>
</xsl:element>
</xsl:template>

<xsl:template match="div|div0|div1|div2|div3|div4|div5|div6|div7|titlePage|argument">
<xsl:element name="div">
<xsl:attribute name="class"><xsl:choose><xsl:when test="@type"><xsl:value-of select="@type" /></xsl:when><xsl:otherwise>unspecified</xsl:otherwise></xsl:choose></xsl:attribute>
<xsl:call-template name="metadata_link"/>
<xsl:call-template name="haalPbNietBinnen"/>
<xsl:apply-templates/>
</xsl:element>
</xsl:template>


<!-- ToDo named entity standoff annotation-->
<!-- ToDo: untokenized text: not possible in folia (comment by proycon: yes it is, just associate <t> elements with higher-level structural elements) -->

<xsl:template match="w|pc">
<w>
    <xsl:if test="@xml:id">
    <xsl:attribute name="xml:id">
    <xsl:value-of select="@xml:id"/>
    </xsl:attribute>
    </xsl:if>
    <t><xsl:apply-templates/></t>
    <xsl:if test="@lemma">
    <lemma><xsl:attribute name="class"><xsl:value-of select="@lemma"/></xsl:attribute></lemma>
    </xsl:if>
    <xsl:if test="@type">
    <pos><xsl:attribute name="class"><xsl:value-of select="@type"/></xsl:attribute></pos>
    </xsl:if>
</w>
</xsl:template>

<xsl:template match="s">
        <s>
               <xsl:call-template name="setId"/>
               <xsl:apply-templates/>
        </s>
    <xsl:if test="./name">
       <folia:entities>
        <xsl:for-each select="./name">
          <folia:entity>
                <xsl:attribute name="class"><xsl:value-of select="@type"/></xsl:attribute>
                <folia:feat subset='normalizedForm'>
                <xsl:attribute name='class'><xsl:for-each select="./w"><xsl:value-of select="./text()"/><xsl:if test="position() &lt; last()"><xsl:text> </xsl:text></xsl:if></xsl:for-each></xsl:attribute>
                </folia:feat>
                <xsl:for-each select="./w">
                <folia:wref>
                        <xsl:attribute name="id"><xsl:value-of select="@id"/></xsl:attribute>
                        <xsl:attribute name="t"><xsl:value-of select="./text()"/></xsl:attribute>
                </folia:wref>
                </xsl:for-each>
          </folia:entity>
        </xsl:for-each>
        </folia:entities>
     </xsl:if>
  </xsl:template>

<xsl:template match="lb"><br/></xsl:template>
<xsl:template match="cb"><br class='cb'/></xsl:template>

<!--
pb n="199" facs="http://resources.huygens.knaw.nl/retroapp/service_declercq/5/images/FV.003.tiff"/>
-->


<xsl:template name="pb">
<br newpage="yes" pagenr="{@n}"/> <!-- xlink:type="simple" xlink:href="{@facs}"/> -->
</xsl:template>



<xsl:template match="pb|div//pb|div1//pb|div2//pb|div3//pb|titlePage//pb|p//pb|trailer//pb|closer//pb">
<xsl:call-template name="pb"/>
</xsl:template>

<xsl:template match="pb/maarnietechthoor">
<xsl:if test="not (ancestor::div or ancestor::div1 or ancestor::titlePage or ancestor::p) and (following-sibling::*[1][self::div or self::div1 or self::div2 or self::div3 or self::titlePage])">
<xsl:comment>verplaatste pagebreak</xsl:comment>
</xsl:if>
<xsl:if test="ancestor::div or ancestor::titlePage or ancestor::div1">
<xsl:comment>legale pagebreak</xsl:comment>
</xsl:if>
<xsl:if test="not (ancestor::div or ancestor::div1 or ancestor::titlePage or ancestor::pb) and not(following-sibling::*[1][self::div or self::div1 or self::div2 or self::div3 or self::titlePage])">
<xsl:comment>verloren pagebreak</xsl:comment>
</xsl:if>
</xsl:template>

<xsl:template name="haalPbNietBinnen"/>

<xsl:template name="haalPbBinnen">
<xsl:for-each select="preceding-sibling::*[1]">
<xsl:if test="self::pb and (not(ancestor::div)) and (not(ancestor::div1))  and (not(ancestor::titlePage))">
<xsl:comment>opgeviste pagebreak:</xsl:comment>
<xsl:call-template name="pb"/>
</xsl:if>
</xsl:for-each>
</xsl:template>



<xsl:template name="haalPbBinnenInCel">
<xsl:for-each select="..">
<xsl:for-each select="preceding-sibling::*[1]">
<xsl:if test="self::pb">
<xsl:comment>opgeviste pagebreak naar cel</xsl:comment>
<xsl:call-template name="pb"/>
</xsl:if>
</xsl:for-each>
</xsl:for-each>
</xsl:template>


<xsl:template match="text/pb|table/pb|row/pb|list/lb"><xsl:comment>Deze doen we mooi niet hoor!</xsl:comment></xsl:template>

<xsl:template match="supplied[./text()='leeg']"/>

<xsl:template match="corr">
<t-correction class="correction" annotator="{@resp}" original="{@sic}"><xsl:apply-templates/></t-correction>
</xsl:template>

<xsl:template match="supplied"><t-correction class="supplied" annotator="{@resp}"><xsl:apply-templates/></t-correction></xsl:template>

<xsl:template match="del"><t-correction class="deletion" annotator="{@resp}" original="{.//text()}"></t-correction></xsl:template>

<xsl:template match="gap">
<xsl:choose>
<xsl:when test="ancestor::p or ancestor::cell or ancestor::head or ancestor::note">
<t-gap annotator="{@resp}" class="{@reason}"/>
</xsl:when>
<xsl:otherwise>
<gap annotator="{@resp}" class="{@reason}"/>
</xsl:otherwise>
</xsl:choose>
</xsl:template>

<xsl:template match="hi"><t-style><xsl:attribute name="class"><xsl:choose><xsl:when test="@rendition"><xsl:value-of select="@rendition"/></xsl:when><xsl:when test="@rend"><xsl:value-of select="@rend"/></xsl:when><xsl:otherwise>unspecified</xsl:otherwise></xsl:choose></xsl:attribute><xsl:apply-templates/></t-style></xsl:template>

<!-- disabled because of XSLT2.0 (proycon)
<xsl:template match="hi[./lb]">
<xsl:variable name="class"><xsl:value-of select="@rendition"/><xsl:value-of select="@rend"/></xsl:variable>
<xsl:for-each-group select="node()" group-ending-with="lb">
<t-style class="{$class}">
<xsl:apply-templates select="current-group()[not(self::lb)]"/>
</t-style>
<xsl:apply-templates select="current-group()[self::lb]"/>
</xsl:for-each-group>
</xsl:template>
-->


<xsl:template match="front|body|back">
<div class="{name(.)}matter">
<xsl:call-template name="haalPbBinnen"/>
<xsl:apply-templates/>
</div>
</xsl:template>

<xsl:template name="annotations">
 <annotations>
  <text-annotation processor="proc.tei2folia.xsl"/>
<!--
 <entity-annotation annotatortype="auto" set="unknown"/>
 <subjectivity-annotation annotatortype="auto" set="unknown"/>
-->
  <division-annotation set="http://rdf.ivdnt.org/nederlab/folia/sets/division"/>
  <xsl:if test="//p">
    <paragraph-annotation processor="proc.tei2folia.xsl"/>
  </xsl:if>
  <xsl:if test="//s">
    <sentence-annotation processor="proc.tei2folia.xsl"/>
  </xsl:if>
  <xsl:if test="//w">
    <token-annotation processor="proc.tei2folia.xsl"/>
  </xsl:if>
  <xsl:if test="//list">
    <list-annotation set="http://rdf.ivdnt.org/nederlab/folia/sets/list" processor="proc.tei2folia.xsl" />
  </xsl:if>
  <xsl:if test="//figure">
    <figure-annotation processor="proc.tei2folia.xsl"/>
  </xsl:if>
  <xsl:if test="//table">
    <table-annotation processor="proc.tei2folia.xsl"/>
  </xsl:if>
  <xsl:if test="//gap">
   <gap-annotation set="http://rdf.ivdnt.org/nederlab/folia/sets/gap" processor="proc.tei2folia.xsl"/>
  </xsl:if>
  <xsl:if test="//hi">
   <style-annotation set="http://rdf.ivdnt.org/nederlab/folia/sets/style" processor="proc.tei2folia.xsl"/>
 </xsl:if>
 <part-annotation annotatortype="auto" set="http://rdf.ivdnt.org/nederlab/folia/sets/part" processor="proc.tei2folia.xsl"/>
 <xsl:if test="//w/@pos">
  <pos-annotation set="unknown" processor="proc.tei2folia.xsl"/>
 </xsl:if>
 <xsl:if test="//w/@lemma">
  <lemma-annotation set="unknown" processor="proc.tei2folia.xsl"/>
 </xsl:if>
<!--
 <whitespace-annotation annotatortype="auto" set="http://rdf.ivdnt.org/nederlab/folia/sets/whitespace"/>
-->
<xsl:if test="//cor|//supplied|//del">
 <correction-annotation annotatortype="auto" set="http://rdf.ivdnt.org/nederlab/folia/sets/correction" processor="proc.tei2folia.xsl"/>
</xsl:if>
<xsl:if test="//note">
 <note-annotation set="http://rdf.ivdnt.org/nederlab/folia/sets/note" processor="proc.tei2folia.xsl"/>
</xsl:if>
 <string-annotation set="http://rdf.ivdnt.org/nederlab/folia/sets/string"/>
<xsl:if test="//sp|//stage">
 <event-annotation annotatortype="auto" set="unknown"/>
</xsl:if>
<xsl:if test="//lb|//pb">
 <linebreak-annotation set="http://rdf.ivdnt.org/nederlab/folia/sets/linebreak"/>
</xsl:if>
   </annotations>
</xsl:template>

<xsl:template name="provenance">
   <provenance>
    <processor xml:id="proc.tei2folia" name="tei2folia" version="0.7.7" host="${host}" user="${user}" src="https://github.com/proycon/foliatools">
        <processor xml:id="proc.tei2folia.xsl" name="tei2folia.xsl" />
    </processor>
   </provenance>
</xsl:template>

<xsl:template match="delSpan">
<xsl:variable name="spanTo"><xsl:value-of select="@spanTo"/></xsl:variable>
<xsl:variable name="end"><xsl:value-of select="following-sibling::anchor[@xml:id=$spanTo]"/></xsl:variable>
<xsl:if test="$end">
<xsl:message>Deleted text: (<xsl:value-of select="name($end)"/>) <xsl:value-of select="$end/preceding-sibling::node()[preceding-sibling::delSpan[@spanTo=$spanTo]]"/>
</xsl:message>
</xsl:if>
</xsl:template>

<xsl:template match="anchor"/>

<xsl:template match="sp">
<xsl:text>
</xsl:text>
<event class="speakerturn">
<xsl:choose>
<xsl:when test=".//speaker/hi">
    <xsl:attribute name="actor"><xsl:value-of select="string(.//speaker/hi)" /></xsl:attribute>
    <xsl:apply-templates/>
</xsl:when>
<xsl:when test=".//speaker">
    <xsl:attribute name="actor"><xsl:value-of select="string(.//speaker)" /></xsl:attribute>
    <xsl:apply-templates/>
</xsl:when>
</xsl:choose>
</event>
</xsl:template>

<xsl:template match="stage">
<event class="stage">
    <xsl:call-template name="pContents"/>
</event>
</xsl:template>

<xsl:template match="*">
<xsl:message>Unknown tag: <xsl:value-of select="name(.)"/></xsl:message>
<xsl:apply-templates/>
</xsl:template>

<xsl:template match="interpGrp/interp"><xsl:variable name="cur"><xsl:value-of select="."/></xsl:variable><xsl:if test="not(../interp[1]=$cur)">|</xsl:if><xsl:apply-templates/></xsl:template>

<xsl:template match="interpGrp/text()"/>

<xsl:template match="interp/text()"><xsl:value-of select="normalize-space(.)"/></xsl:template>

<xsl:template match="add[@resp='transcriber']"/>

<xsl:template match="p//add">
<xsl:message>JAWEL, HET KOMT WEL VOOR!!!!</xsl:message>
<note class="add" annotator="@resp">
<t>
<xsl:apply-templates/>
</t>
</note>
</xsl:template>

<xsl:template match="TEI|TEI.2">
<FoLiA xmlns:xlink="http://www.w3.org/1999/xlink" xmlns="http://ilk.uvt.nl/folia" version="2.0.3" generator="tei2folia.xsl">
  <xsl:attribute name="xml:id"><xsl:value-of select="$docid"/></xsl:attribute>
  <metadata>
    <xsl:call-template name="annotations"/>
    <xsl:call-template name="provenance"/>
    <xsl:for-each select=".//listBibl[@xml:id='inlMetadata']//interpGrp"><meta id="{./@type}"><xsl:apply-templates/></meta></xsl:for-each>
    <xsl:for-each select=".//listBibl[not(@xml:id='inlMetadata')]">
        <submetadata>
            <xsl:attribute name="xml:id"><xsl:value-of select="substring-after(.//interpGrp/@inst[position()=1],'#')"/></xsl:attribute>
            <xsl:for-each select=".//interpGrp"><meta id="{./@type}"><xsl:apply-templates/></meta></xsl:for-each>
       </submetadata>
    </xsl:for-each>
  </metadata>
  <text>
    <xsl:attribute name="xml:id"><xsl:value-of select="$docid"/>.text</xsl:attribute>
    <xsl:apply-templates select="//text/*"/>
  </text>
</FoLiA>
</xsl:template>
</xsl:stylesheet>
