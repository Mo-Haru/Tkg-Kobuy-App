// header profile menu
const anchorEl = document.body.querySelector('#usage-anchor');
const menuEl = document.body.querySelector('#usage-menu');
anchorEl.addEventListener('click', () => { menuEl.open = !menuEl.open; });


// navigation menu toggle
    const main_body = document.getElementById("main_body");
    const navigation = document.getElementById("navigation");
    const menu_toggle = document.getElementById("navi_toggle_button");
    const navi_title_name_h = document.getElementById("navi_title_name_home");
    const navi_title_name_r = document.getElementById("navi_title_name_reserve");
    const navi_title_name_m = document.getElementById("navi_title_name_menuedit");
    const navi_title_name_s = document.getElementById("navi_title_name_sale_option");
    const navi_title_name_ms = document.getElementById("navi_title_name_menu_stock");
    const navi_title_name_c = document.getElementById("navi_title_name_contact");


    menu_toggle.addEventListener("click", toggle_navilist)

    function toggle_navilist() {
        
        navi_title_name_h.classList.toggle("hidden")
        navi_title_name_r.classList.toggle("hidden")
        navi_title_name_m.classList.toggle("hidden")
        navi_title_name_s.classList.toggle("hidden")
        navi_title_name_ms.classList.toggle("hidden")
        navi_title_name_c.classList.toggle("hidden")

        navigation.classList.toggle("navi_narrow")
        main_body.classList.toggle("main_s")

        // 現在の状態をlocalStorageに保存する
        const isNaviNarrow = navigation.classList.contains("navi_narrow");
        localStorage.setItem("isNaviNarrow", isNaviNarrow ? "true" : "false");
    }


// ページ読み込み時にlocalStorageから状態を取得して復元
document.addEventListener("DOMContentLoaded", () => {
    const isNaviNarrow = localStorage.getItem("isNaviNarrow") === "true";
    
    if (isNaviNarrow) {
        navi_title_name_h.classList.add("hidden");
        navi_title_name_r.classList.add("hidden");
        navi_title_name_m.classList.add("hidden");
        navi_title_name_s.classList.add("hidden");
        navi_title_name_ms.classList.add("hidden");
        navi_title_name_c.classList.add("hidden");


        navigation.classList.add("navi_narrow");
        main_body.classList.add("main_s");
    }
});



