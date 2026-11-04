(() => {
    "use strict";

    const element = (tag, className, text) => {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    };
    const shortName = text => text.replace(/^第[一二三四五六七八九十]+[编章]\s*/, "");
    const chainFor = link => {
        const chain = [];
        let item = link.closest("li.chapter-item");
        while (item) {
            const anchor = item.querySelector(":scope > .chapter-link-wrapper > a[href]");
            if (anchor) chain.unshift(anchor);
            item = item.parentElement.closest("li.chapter-item");
        }
        return chain;
    };

    function setupStickyDirectoryHeaders(tree, scrollbox) {
        const branches = [...tree.querySelectorAll("li.chapter-item")].flatMap(item => {
            if (!item.querySelector(":scope > ol")) return [];
            const wrapper = item.querySelector(":scope > .chapter-link-wrapper");
            const anchor = wrapper.querySelector("a[href]");
            const parents = chainFor(anchor).slice(0, -1).map(link => link.parentElement);
            wrapper.classList.add("directory-branch-header");
            wrapper.style.setProperty("--directory-sticky-layer", 10 - parents.length);
            return [{ wrapper, parents }];
        });
        const updateOffsets = () => {
            // Read all row heights before writing offsets; wrapping can change on resize.
            const heights = new Map(branches.map(({ wrapper }) => [wrapper, wrapper.getBoundingClientRect().height]));
            branches.forEach(({ wrapper, parents }) => {
                const top = parents.reduce((sum, parent) => sum + (heights.get(parent) || 0), 0);
                wrapper.style.setProperty("--directory-sticky-top", `${top}px`);
            });
        };
        const observer = new ResizeObserver(updateOffsets);
        branches.forEach(({ wrapper }) => observer.observe(wrapper));
        updateOffsets();
        tree.addEventListener("click", event => {
            const toggle = event.target.closest(".chapter-fold-toggle");
            if (!toggle) return;
            const wrapper = toggle.parentElement;
            const before = wrapper.getBoundingClientRect().top;
            // Keep the original row in view when collapsing its long subtree.
            requestAnimationFrame(() => {
                scrollbox.scrollTop += wrapper.getBoundingClientRect().top - before;
            });
        }, { capture: true });
    }

    function setupDirectory(root) {
        const sidebar = document.querySelector("#mdbook-sidebar");
        const scrollbox = sidebar?.querySelector(".sidebar-scrollbox");
        const tree = scrollbox?.querySelector("ol.chapter");
        if (!tree) return [];

        const anchors = [...tree.querySelectorAll(".chapter-link-wrapper > a[href]")];
        const current = anchors.find(link => link.classList.contains("active"));
        const currentChain = current ? chainFor(current) : [];
        const entries = anchors.map(link => ({
            title: shortName(link.textContent.trim()),
            href: link.href,
            chain: chainFor(link),
        }));

        entries.forEach(({ chain }, index) => {
            const link = anchors[index];
            const item = link.closest("li.chapter-item");
            if (chain.length === 3) {
                const children = item.querySelectorAll(":scope > ol > li.chapter-item");
                if (children.length) {
                    const badge = element("span", "chapter-count", children.length);
                    const toggle = link.parentElement.querySelector(":scope > .chapter-fold-toggle");
                    link.parentElement.insertBefore(badge, toggle);
                }
            }
            if (currentChain.includes(link)) item.classList.add("current-branch");
        });
        current?.setAttribute("aria-current", "page");

        const header = element("div", "directory-header");
        const brand = element("a", "site-brand");
        brand.href = `${root}index.html`;
        brand.append(element("span", "brand-seal", "食"));
        const brandText = element("span", "brand-name", "食单集注");
        brand.append(brandText);
        header.append(brand);

        const filter = element("input", "directory-filter");
        filter.id = "directory-filter";
        filter.type = "search";
        filter.placeholder = "查找菜名或分类…";
        filter.autocomplete = "off";
        filter.setAttribute("aria-label", "查找菜名或分类");
        filter.setAttribute("aria-controls", "directory-results");
        const status = element("p", "directory-status");
        status.setAttribute("role", "status");
        status.hidden = true;
        header.append(filter);
        sidebar.insertBefore(header, scrollbox);
        sidebar.classList.add("recipe-directory");
        sidebar.setAttribute("aria-label", "菜谱目录");

        const results = element("ul", "directory-results");
        results.id = "directory-results";
        results.hidden = true;
        scrollbox.append(status, results);
        let directoryScrollTop = 0;
        filter.addEventListener("input", () => {
            const query = filter.value.trim().toLocaleLowerCase();
            const wasSearching = tree.hidden;
            if (query && !wasSearching) directoryScrollTop = scrollbox.scrollTop;
            tree.hidden = Boolean(query);
            results.hidden = !query;
            status.hidden = !query;
            results.replaceChildren();
            if (!query) {
                status.textContent = "";
                if (wasSearching) scrollbox.scrollTop = directoryScrollTop;
                return;
            }
            const matches = entries.filter(entry => entry.title.toLocaleLowerCase().includes(query));
            status.textContent = matches.length
                ? `找到 ${matches.length} 项${matches.length > 50 ? "，显示前 50 项" : ""}`
                : "没有找到，试试更短的菜名";
            matches.slice(0, 50).forEach(entry => {
                const item = element("li");
                const link = element("a", "", entry.title);
                link.href = entry.href;
                const context = entry.chain.slice(1, -1).map(a => shortName(a.textContent.trim())).join(" / ");
                if (context) link.append(element("small", "", context));
                item.append(link);
                results.append(item);
            });
            scrollbox.scrollTop = 0;
        });
        filter.addEventListener("keydown", event => {
            if (event.key === "Escape") {
                event.stopPropagation();
                event.preventDefault();
                filter.value = "";
                filter.dispatchEvent(new Event("input"));
            }
        });
        setupStickyDirectoryHeaders(tree, scrollbox);
        let positioned = false;
        const positionCurrent = () => {
            if (!current || !scrollbox.clientHeight) return;
            const parentsHeight = currentChain.slice(0, -1).reduce(
                (sum, link) => sum + link.parentElement.getBoundingClientRect().height, 0
            );
            const target = Math.max(parentsHeight + 8, scrollbox.clientHeight / 3);
            const top = current.getBoundingClientRect().top - scrollbox.getBoundingClientRect().top;
            scrollbox.scrollTop += top - target;
            positioned = true;
        };
        requestAnimationFrame(positionCurrent);
        document.querySelector("#mdbook-sidebar-toggle-anchor")?.addEventListener("change", event => {
            if (event.target.checked && !positioned) requestAnimationFrame(positionCurrent);
        });
        return currentChain;
    }

    function setupBreadcrumbs(main, chain) {
        if (!chain.length) return;
        const breadcrumbs = element("nav", "recipe-breadcrumbs");
        breadcrumbs.setAttribute("aria-label", "当前位置");
        chain.forEach((anchor, index) => {
            if (index > 0) breadcrumbs.append(element("span", "breadcrumb-separator", "/"));
            const last = index === chain.length - 1;
            const item = element(last ? "span" : "a", "", shortName(anchor.textContent.trim()));
            if (last) item.setAttribute("aria-current", "page");
            else item.href = anchor.href;
            breadcrumbs.append(item);
        });
        main.prepend(breadcrumbs);
    }

    function setupCategoryFilter() {
        const input = document.querySelector("#category-filter");
        if (!input) return;
        const items = [...document.querySelectorAll("#category-recipes > li")];
        const count = document.querySelector("#category-result-count");
        const empty = document.querySelector("#category-empty");
        input.closest(".recipe-filter").hidden = false;
        const update = () => {
            const query = input.value.trim().toLocaleLowerCase();
            let visible = 0;
            items.forEach(item => {
                item.hidden = !item.textContent.toLocaleLowerCase().includes(query);
                if (!item.hidden) visible++;
            });
            count.textContent = query ? `${visible} / ${items.length} 道` : `共${items.length}道`;
            empty.hidden = visible > 0;
        };
        input.addEventListener("input", update);
        update();
    }

    function setupReadingOutline(main) {
        const sections = [...main.querySelectorAll("h2")];
        if (!sections.length) return;
        const hasVersions = sections.some(heading => heading.textContent.trim().endsWith("版本"));
        const layout = element("div", "recipe-reading-layout");
        const article = element("article", "recipe-article");
        article.append(...main.childNodes);
        const aside = element("aside", "recipe-outline");
        const navigation = element("nav");
        navigation.setAttribute("aria-label", hasVersions ? "来源版本与段落" : "菜谱段落");
        const list = element("ul", "outline-list");
        const jumps = element("nav", "version-jumps");
        jumps.setAttribute("aria-label", hasVersions ? "来源版本目录" : "菜谱段落目录");
        const jumpList = element("ul");
        jumps.append(jumpList);
        const groups = new Map();
        const outlineLinks = new Map();
        let group;
        let sublist;
        const headings = [...article.querySelectorAll("h2, h3")];
        headings.forEach(heading => {
            if (heading.tagName === "H2") {
                group = element("li", "outline-group");
                sublist = element("ul");
                list.append(group);
                const jump = element("a", "", heading.textContent.trim());
                jump.href = `#${heading.id}`;
                const jumpItem = element("li");
                jumpItem.append(jump);
                jumpList.append(jumpItem);
                heading.classList.add("recipe-version");
            }
            const link = element("a", "", heading.textContent.trim());
            link.href = `#${heading.id}`;
            outlineLinks.set(heading, link);
            groups.set(heading, group);
            if (heading.tagName === "H2") group.append(link, sublist);
            else {
                const item = element("li");
                item.append(link);
                sublist.append(item);
            }
        });
        article.querySelector("h1")?.after(jumps);
        navigation.append(list);
        aside.append(navigation);
        layout.append(article, aside);
        main.append(layout);

        const update = () => {
            const active = headings.filter(heading => heading.getBoundingClientRect().top <= 150).at(-1) || headings[0];
            groups.forEach(groupItem => groupItem.classList.remove("is-active"));
            groups.get(active)?.classList.add("is-active");
            outlineLinks.forEach((link, heading) => {
                link.classList.toggle("is-active", heading === active);
                if (heading === active) link.setAttribute("aria-current", "location");
                else link.removeAttribute("aria-current");
            });
        };
        let scheduled = false;
        window.addEventListener("scroll", () => {
            if (scheduled) return;
            scheduled = true;
            requestAnimationFrame(() => { update(); scheduled = false; });
        }, { passive: true });
        window.addEventListener("resize", update);
        update();
    }

    function init() {
        const main = document.querySelector("#mdbook-content main");
        if (!main || location.pathname.endsWith("print.html")) return;
        document.body.classList.add("recipe-site");
        const root = document.querySelector('meta[name="recipe-root"]')?.content || "";
        const chain = setupDirectory(root);
        setupBreadcrumbs(main, chain);
        setupCategoryFilter();
        if (chain.length >= 4) setupReadingOutline(main);
        const search = document.querySelector("#mdbook-searchbar");
        if (search) search.placeholder = "搜索全书内容…";
        const toggle = document.querySelector("#mdbook-sidebar-toggle");
        toggle?.setAttribute("aria-label", "展开或收起目录");
        toggle?.setAttribute("title", "展开或收起目录");
    }
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
    else init();
})();
